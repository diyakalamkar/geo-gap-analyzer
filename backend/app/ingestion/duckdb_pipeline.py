"""
duckdb_pipeline.py

Ingest + clean raw Amazon Reviews JSONL into Parquet and register
the cleaned data in DuckDB.

Memory-safe architecture:
- DuckDB memory_limit = 3GB
- threads = 1
- preserve_insertion_order = false
- temporary spill directory = data/processed/duckdb_tmp
- large review files are first hash-partitioned into Parquet
- deduplication is performed one partition at a time
- metadata is also hash-partitioned before deduplication

This avoids running a large ROW_NUMBER() operation over the
entire 10+ GB Beauty_and_Personal_Care review file at once.
"""

from pathlib import Path
from typing import Optional
import shutil

import duckdb

from .config import CLEAN_DIR, DB_PATH, RAW_DIR


# ---------------------------------------------------------------------
# CONFIGURATION
# ---------------------------------------------------------------------

# Number of deterministic partitions.
#
# The deduplication key is:
#     user_id + asin + timestamp
#
# All records with the same key go to the same partition.
# Therefore partition-wise deduplication is equivalent to
# deduplicating the complete dataset.
DEDUP_PARTITIONS = 64

MAX_TEMP_SIZE = "20GB"


# ---------------------------------------------------------------------
# REVIEW SCHEMA
# ---------------------------------------------------------------------

REVIEW_COLUMNS = {
    "rating": "DOUBLE",
    "title": "VARCHAR",
    "text": "VARCHAR",
    "asin": "VARCHAR",
    "parent_asin": "VARCHAR",
    "user_id": "VARCHAR",
    "timestamp": "BIGINT",
    "helpful_vote": "BIGINT",
    "verified_purchase": "BOOLEAN",
}


# ---------------------------------------------------------------------
# METADATA SCHEMA
# ---------------------------------------------------------------------

META_COLUMNS = {
    "parent_asin": "VARCHAR",
    "title": "VARCHAR",
    "store": "VARCHAR",
    "main_category": "VARCHAR",
    "average_rating": "DOUBLE",
    "rating_number": "BIGINT",
}


# ---------------------------------------------------------------------
# DUCKDB CONNECTION
# ---------------------------------------------------------------------

def get_connection(
    read_only: bool = False,
) -> duckdb.DuckDBPyConnection:
    """
    Open the persistent DuckDB database with conservative
    memory settings.

    Large intermediate operations can spill to disk.
    """

    CLEAN_DIR.mkdir(parents=True, exist_ok=True)

    temp_dir = CLEAN_DIR.parent / "duckdb_tmp"
    temp_dir.mkdir(parents=True, exist_ok=True)

    con = duckdb.connect(
        str(DB_PATH),
        read_only=read_only,
    )

    con.execute("SET memory_limit = '3GB'")
    con.execute("SET threads = 1")
    con.execute("SET preserve_insertion_order = false")

    temp_sql_path = (
        str(temp_dir)
        .replace("\\", "/")
        .replace("'", "''")
    )

    con.execute(
        f"SET temp_directory = '{temp_sql_path}'"
    )

    con.execute(
        f"SET max_temp_directory_size = '{MAX_TEMP_SIZE}'"
    )

    return con


# ---------------------------------------------------------------------
# FILE HELPERS
# ---------------------------------------------------------------------

def find_local_file(
    directory: Path,
    stem: str,
) -> Optional[Path]:
    """
    Case-insensitive lookup of '<stem>.jsonl'.
    """

    target = f"{stem}.jsonl".lower()

    for p in directory.glob("*.jsonl"):
        if p.name.lower() == target:
            return p

    return None


def _sql_path(p: Path) -> str:
    """
    Convert a Windows Path into a SQL-safe path.
    """

    return (
        str(p)
        .replace("\\", "/")
        .replace("'", "''")
    )


def _columns_literal(cols: dict) -> str:
    """
    Convert a Python dictionary schema into DuckDB's
    explicit JSON schema literal.
    """

    return (
        "{"
        + ", ".join(
            f"'{key}': '{value}'"
            for key, value in cols.items()
        )
        + "}"
    )


def _remove_directory(path: Path) -> None:
    """
    Remove an intermediate directory if it exists.
    """

    if path.exists():
        shutil.rmtree(path)

    path.mkdir(parents=True, exist_ok=True)


def _remove_file(path: Path) -> None:
    """
    Remove a file if it exists.
    """

    if path.exists():
        path.unlink()


# ---------------------------------------------------------------------
# REVIEW CLEANING
# ---------------------------------------------------------------------

def clean_reviews(
    category: str,
    raw_path: Optional[Path] = None,
) -> Path:
    """
    Clean one category's raw review JSONL into:

        data/processed/reviews_clean/<category>.parquet

    Processing:

    1. Read JSONL using an explicit schema.
    2. Count raw rows.
    3. Filter invalid reviews.
    4. Hash-partition records into 64 Parquet partitions.
    5. Deduplicate one partition at a time.
    6. Convert epoch milliseconds to TIMESTAMP.
    7. Remove HTML tags.
    8. Normalize whitespace.
    9. Build full_text for VADER.
    10. Create deterministic review_id.
    11. Merge deduplicated partitions into final Parquet.

    The important memory fix is that ROW_NUMBER() is never run
    over the entire 10+ GB category simultaneously.
    """

    raw_path = (
        raw_path
        or find_local_file(RAW_DIR, category)
    )

    if raw_path is None or not raw_path.exists():
        raise FileNotFoundError(
            f"No review jsonl for {category!r} "
            f"in {RAW_DIR}"
        )

    CLEAN_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    out_path = (
        CLEAN_DIR / f"{category}.parquet"
    )

    # -------------------------------------------------------------
    # Intermediate directories
    # -------------------------------------------------------------

    stage_dir = (
        CLEAN_DIR.parent
        / "review_stage"
        / category
    )

    dedup_dir = (
        CLEAN_DIR.parent
        / "review_dedup"
        / category
    )

    _remove_directory(stage_dir)
    _remove_directory(dedup_dir)

    _remove_file(out_path)

    con = get_connection()

    try:
        raw_sql = _sql_path(raw_path)
        out_sql = _sql_path(out_path)

        stage_sql = _sql_path(stage_dir)
        dedup_sql = _sql_path(dedup_dir)

        columns_sql = _columns_literal(
            REVIEW_COLUMNS
        )

        print()
        print(
            f"[duckdb_pipeline] "
            f"Starting staged cleaning for {category}"
        )

        print(
            f"[duckdb_pipeline] "
            f"Source: {raw_path}"
        )

        # ---------------------------------------------------------
        # STEP 1 — Count raw records
        # ---------------------------------------------------------

        print(
            "[duckdb_pipeline] Counting raw JSONL rows..."
        )

        n_raw = con.execute(
            f"""
            SELECT count(*)
            FROM read_json(
                '{raw_sql}',
                format = 'newline_delimited',
                columns = {columns_sql}
            )
            """
        ).fetchone()[0]

        print(
            f"[duckdb_pipeline] "
            f"{category}: {n_raw:,} raw rows"
        )

        # ---------------------------------------------------------
        # STEP 2 — Filter + hash partition
        # ---------------------------------------------------------
        #
        # IMPORTANT:
        #
        # We do NOT deduplicate here.
        #
        # Instead, every duplicate key:
        #
        #     user_id + asin + timestamp
        #
        # gets the same partition_id.
        #
        # This allows exact deduplication later while keeping
        # each ROW_NUMBER operation small.
        # ---------------------------------------------------------

        print(
            f"[duckdb_pipeline] "
            f"Creating {DEDUP_PARTITIONS} "
            f"disk-backed review partitions..."
        )

        stage_query = f"""
        COPY (
            SELECT
                rating,
                title,
                text,
                asin,
                parent_asin,
                user_id,
                timestamp,
                helpful_vote,
                verified_purchase,

                CAST(
                    hash(
                        concat_ws(
                            '|',
                            coalesce(user_id, ''),
                            coalesce(asin, ''),
                            CAST(timestamp AS VARCHAR)
                        )
                    ) % {DEDUP_PARTITIONS}
                    AS INTEGER
                ) AS partition_id

            FROM read_json(
                '{raw_sql}',
                format = 'newline_delimited',
                columns = {columns_sql}
            )

            WHERE rating BETWEEN 1 AND 5
              AND parent_asin IS NOT NULL
              AND timestamp IS NOT NULL
        )
        TO '{stage_sql}'
        (
            FORMAT PARQUET,
            PARTITION_BY (partition_id),
            COMPRESSION ZSTD
        )
        """

        con.execute(stage_query)

        stage_files = sorted(
            stage_dir.rglob("*.parquet")
        )

        if not stage_files:
            raise RuntimeError(
                f"No staged Parquet partitions were created "
                f"for {category}"
            )

        print(
            f"[duckdb_pipeline] "
            f"{category}: "
            f"{len(stage_files)} staged partitions created"
        )

        # ---------------------------------------------------------
        # STEP 3 — Count filtered rows
        # ---------------------------------------------------------

        filtered_glob = _sql_path(
            stage_dir / "**" / "*.parquet"
        )

        n_filtered = con.execute(
            f"""
            SELECT count(*)
            FROM read_parquet(
                '{filtered_glob}'
            )
            """
        ).fetchone()[0]

        print(
            f"[duckdb_pipeline] "
            f"{category}: "
            f"{n_filtered:,} rows after validation"
        )

        # ---------------------------------------------------------
        # STEP 4 — Deduplicate one partition at a time
        # ---------------------------------------------------------

        total_clean = 0

        for index, stage_file in enumerate(
            stage_files,
            start=1,
        ):
            stage_file_sql = _sql_path(stage_file)

            dedup_file = (
                dedup_dir
                / f"part_{index:03d}.parquet"
            )

            dedup_file_sql = _sql_path(
                dedup_file
            )

            print(
                f"[duckdb_pipeline] "
                f"{category}: "
                f"deduplicating partition "
                f"{index}/{len(stage_files)}..."
            )

            dedup_query = f"""
            COPY (
                WITH ranked AS (
                    SELECT
                        rating,
                        title,
                        text,
                        asin,
                        parent_asin,
                        user_id,
                        timestamp,
                        helpful_vote,
                        verified_purchase,

                        row_number() OVER (
                            PARTITION BY
                                user_id,
                                asin,
                                timestamp
                            ORDER BY
                                length(
                                    coalesce(text, '')
                                ) DESC
                        ) AS duplicate_rank

                    FROM read_parquet(
                        '{stage_file_sql}'
                    )
                ),

                deduplicated AS (
                    SELECT
                        rating,
                        title,
                        text,
                        asin,
                        parent_asin,
                        user_id,
                        timestamp,
                        helpful_vote,
                        verified_purchase
                    FROM ranked
                    WHERE duplicate_rank = 1
                )

                SELECT
                    md5(
                        concat_ws(
                            '|',
                            '{category}',
                            user_id,
                            asin,
                            CAST(timestamp AS VARCHAR)
                        )
                    ) AS review_id,

                    '{category}' AS category,

                    parent_asin,
                    asin,
                    user_id,
                    rating,

                    to_timestamp(
                        timestamp / 1000.0
                    )::TIMESTAMP AS review_ts,

                    title,
                    text,

                    trim(
                        regexp_replace(
                            regexp_replace(
                                concat_ws(
                                    '. ',
                                    nullif(
                                        trim(title),
                                        ''
                                    ),
                                    nullif(
                                        trim(text),
                                        ''
                                    )
                                ),
                                '<[^>]+>',
                                ' ',
                                'g'
                            ),
                            '\\s+',
                            ' ',
                            'g'
                        )
                    ) AS full_text,

                    coalesce(
                        helpful_vote,
                        0
                    ) AS helpful_vote,

                    coalesce(
                        verified_purchase,
                        FALSE
                    ) AS verified_purchase

                FROM deduplicated
            )
            TO '{dedup_file_sql}'
            (
                FORMAT PARQUET,
                COMPRESSION ZSTD
            )
            """

            con.execute(dedup_query)

            partition_count = con.execute(
                f"""
                SELECT count(*)
                FROM read_parquet(
                    '{dedup_file_sql}'
                )
                """
            ).fetchone()[0]

            total_clean += partition_count

            print(
                f"[duckdb_pipeline] "
                f"{category}: partition "
                f"{index}/{len(stage_files)} -> "
                f"{partition_count:,} rows"
            )

        # ---------------------------------------------------------
        # STEP 5 — Merge deduplicated partitions
        # ---------------------------------------------------------

        print(
            f"[duckdb_pipeline] "
            f"{category}: merging deduplicated partitions..."
        )

        dedup_glob = _sql_path(
            dedup_dir / "*.parquet"
        )

        merge_query = f"""
        COPY (
            SELECT *
            FROM read_parquet(
                '{dedup_glob}'
            )
        )
        TO '{out_sql}'
        (
            FORMAT PARQUET,
            COMPRESSION ZSTD
        )
        """

        con.execute(merge_query)

        # ---------------------------------------------------------
        # STEP 6 — Verify final output
        # ---------------------------------------------------------

        n_clean = con.execute(
            f"""
            SELECT count(*)
            FROM read_parquet(
                '{out_sql}'
            )
            """
        ).fetchone()[0]

        print()
        print(
            f"[duckdb_pipeline] "
            f"{category}: "
            f"{n_raw:,} raw rows -> "
            f"{n_filtered:,} valid rows -> "
            f"{n_clean:,} clean rows "
            f"({n_raw - n_clean:,} dropped) "
            f"-> {out_path.name}"
        )

        # ---------------------------------------------------------
        # STEP 7 — Remove intermediate review files
        # ---------------------------------------------------------

        print(
            f"[duckdb_pipeline] "
            f"{category}: removing intermediate partitions..."
        )

        shutil.rmtree(stage_dir)
        shutil.rmtree(dedup_dir)

        print(
            f"[duckdb_pipeline] "
            f"{category}: cleaning completed successfully."
        )

        return out_path

    finally:
        con.close()


# ---------------------------------------------------------------------
# PRODUCT METADATA
# ---------------------------------------------------------------------

def load_product_dim(
    con: duckdb.DuckDBPyConnection,
    category: str,
    meta_path: Optional[Path] = None,
) -> bool:
    """
    Load Amazon product metadata for one category.

    The metadata provides the `store` field used by the
    brand normalization stage.

    Metadata is also processed in deterministic partitions so
    the 2.6+ GB metadata file does not require a full-dataset
    window operation.
    """

    meta_path = (
        meta_path
        or find_local_file(
            RAW_DIR,
            f"meta_{category}",
        )
    )

    if meta_path is None:
        print(
            f"[duckdb_pipeline] "
            f"no metadata file for {category}: "
            f"brand step will be skipped"
        )
        return False

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS product_dim (
            category VARCHAR,
            parent_asin VARCHAR,
            product_title VARCHAR,
            store VARCHAR,
            main_category VARCHAR,
            meta_average_rating DOUBLE,
            meta_rating_number BIGINT
        )
        """
    )

    # Replace this category if previously processed.
    con.execute(
        "DELETE FROM product_dim WHERE category = ?",
        [category],
    )

    meta_sql = _sql_path(meta_path)
    columns_sql = _columns_literal(
        META_COLUMNS
    )

    # -------------------------------------------------------------
    # Metadata staging directories
    # -------------------------------------------------------------

    meta_stage_dir = (
        CLEAN_DIR.parent
        / "metadata_stage"
        / category
    )

    meta_dedup_dir = (
        CLEAN_DIR.parent
        / "metadata_dedup"
        / category
    )

    _remove_directory(meta_stage_dir)
    _remove_directory(meta_dedup_dir)

    meta_stage_sql = _sql_path(
        meta_stage_dir
    )

    print()
    print(
        f"[duckdb_pipeline] "
        f"Staging metadata for {category}..."
    )

    # -------------------------------------------------------------
    # STEP 1 — Partition metadata
    # -------------------------------------------------------------

    metadata_stage_query = f"""
    COPY (
        SELECT
            parent_asin,
            title,
            store,
            main_category,
            average_rating,
            rating_number,

            CAST(
                hash(
                    coalesce(
                        parent_asin,
                        ''
                    )
                ) % {DEDUP_PARTITIONS}
                AS INTEGER
            ) AS partition_id

        FROM read_json(
            '{meta_sql}',
            format = 'newline_delimited',
            columns = {columns_sql}
        )

        WHERE parent_asin IS NOT NULL
    )
    TO '{meta_stage_sql}'
    (
        FORMAT PARQUET,
        PARTITION_BY (partition_id),
        COMPRESSION ZSTD
    )
    """

    con.execute(
        metadata_stage_query
    )

    meta_stage_files = sorted(
        meta_stage_dir.rglob("*.parquet")
    )

    if not meta_stage_files:
        print(
            f"[duckdb_pipeline] "
            f"metadata staging produced no files "
            f"for {category}"
        )

        shutil.rmtree(meta_stage_dir)

        return False

    print(
        f"[duckdb_pipeline] "
        f"{category}: "
        f"{len(meta_stage_files)} metadata partitions"
    )

    # -------------------------------------------------------------
    # STEP 2 — Deduplicate metadata partition by partition
    # -------------------------------------------------------------

    for index, stage_file in enumerate(
        meta_stage_files,
        start=1,
    ):
        stage_file_sql = _sql_path(
            stage_file
        )

        dedup_file = (
            meta_dedup_dir
            / f"part_{index:03d}.parquet"
        )

        dedup_file_sql = _sql_path(
            dedup_file
        )

        print(
            f"[duckdb_pipeline] "
            f"{category}: metadata partition "
            f"{index}/{len(meta_stage_files)}..."
        )

        metadata_dedup_query = f"""
        COPY (
            WITH ranked AS (
                SELECT
                    parent_asin,
                    title,
                    store,
                    main_category,
                    average_rating,
                    rating_number,

                    row_number() OVER (
                        PARTITION BY parent_asin
                        ORDER BY
                            rating_number DESC NULLS LAST
                    ) AS duplicate_rank

                FROM read_parquet(
                    '{stage_file_sql}'
                )
            )

            SELECT
                parent_asin,
                title,
                store,
                main_category,
                average_rating,
                rating_number

            FROM ranked

            WHERE duplicate_rank = 1
        )
        TO '{dedup_file_sql}'
        (
            FORMAT PARQUET,
            COMPRESSION ZSTD
        )
        """

        con.execute(
            metadata_dedup_query
        )

    # -------------------------------------------------------------
    # STEP 3 — Insert metadata into product_dim
    # -------------------------------------------------------------

    meta_dedup_glob = _sql_path(
        meta_dedup_dir / "*.parquet"
    )

    con.execute(
        f"""
        INSERT INTO product_dim
        SELECT
            '{category}' AS category,
            parent_asin,
            title AS product_title,
            store,
            main_category,
            average_rating AS meta_average_rating,
            rating_number AS meta_rating_number

        FROM read_parquet(
            '{meta_dedup_glob}'
        )
        """
    )

    # -------------------------------------------------------------
    # STEP 4 — Verify
    # -------------------------------------------------------------

    n = con.execute(
        """
        SELECT count(*)
        FROM product_dim
        WHERE category = ?
        """,
        [category],
    ).fetchone()[0]

    print(
        f"[duckdb_pipeline] "
        f"{category}: "
        f"{n:,} products loaded into product_dim"
    )

    # -------------------------------------------------------------
    # STEP 5 — Remove metadata intermediates
    # -------------------------------------------------------------

    shutil.rmtree(meta_stage_dir)
    shutil.rmtree(meta_dedup_dir)

    print(
        f"[duckdb_pipeline] "
        f"{category}: metadata processing completed."
    )

    return True


# ---------------------------------------------------------------------
# CLEAN REVIEW VIEW
# ---------------------------------------------------------------------

def register_clean_views(
    con: duckdb.DuckDBPyConnection,
) -> None:
    """
    Expose all cleaned review Parquet files as one DuckDB view.
    """

    glob = _sql_path(
        CLEAN_DIR / "*.parquet"
    )

    con.execute(
        f"""
        CREATE OR REPLACE VIEW reviews_clean AS
        SELECT *
        FROM read_parquet(
            '{glob}'
        )
        """
    )


# ---------------------------------------------------------------------
# DIRECT EXECUTION
# ---------------------------------------------------------------------

if __name__ == "__main__":

    from .config import CATEGORIES

    for category in CATEGORIES:

        try:
            clean_reviews(category)

        except FileNotFoundError as exc:
            print(exc)