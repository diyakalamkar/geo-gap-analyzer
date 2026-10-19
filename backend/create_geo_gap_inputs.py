from pathlib import Path
import duckdb

from app.ingestion.config import DB_PATH, EXPORT_DIR


OUTPUT_FILE = EXPORT_DIR / "geo_gap_product_ground_truth.parquet"


def main():
    print("=" * 70)
    print("GEO-GAP INPUT BUILDER")
    print("=" * 70)

    con = duckdb.connect(str(DB_PATH))

    # ---------------------------------------------------------
    # Check required tables
    # ---------------------------------------------------------

    tables = {
        row[0]
        for row in con.execute("SHOW TABLES").fetchall()
    }

    required = {
        "merit_product",
        "product_dim",
        "recency_momentum_product",
    }

    missing = required - tables

    if missing:
        raise RuntimeError(
            "Required tables are missing: "
            + ", ".join(sorted(missing))
        )

    print("[OK] Required DuckDB tables found.")

    # ---------------------------------------------------------
    # Build compact product-level ground truth
    # ---------------------------------------------------------

    query = """
    SELECT
        m.category,
        m.parent_asin,
        d.product_title,
        d.store,

        m.merit_rank_in_category AS ground_truth_rank,
        m.merit_score AS ground_truth_merit_score,

        m.n_reviews,
        m.avg_rating,
        m.recency_weighted_rating,
        m.recency_factor,

        m.avg_sentiment,
        m.pct_positive,
        m.pct_neutral,
        m.pct_negative,

        m.verified_share,
        m.total_helpful_votes,

        m.first_review_ts,
        m.last_review_ts,

        r.n_recent,
        r.n_previous,
        r.rating_recent,
        r.rating_previous,
        r.rating_change,
        r.sentiment_recent,
        r.sentiment_previous,
        r.volume_ratio

    FROM merit_product m

    LEFT JOIN product_dim d
        ON d.category = m.category
        AND d.parent_asin = m.parent_asin

    LEFT JOIN recency_momentum_product r
        ON r.category = m.category
        AND r.parent_asin = m.parent_asin

    WHERE m.meets_min_reviews

    ORDER BY
        m.category,
        m.merit_rank_in_category
    """

    print("[INFO] Building product ground-truth dataset...")

    con.execute(
        f"""
        COPY (
            {query}
        )
        TO '{OUTPUT_FILE.as_posix()}'
        (
            FORMAT PARQUET,
            COMPRESSION ZSTD
        )
        """
    )

    # ---------------------------------------------------------
    # Validation
    # ---------------------------------------------------------

    count = con.execute(
        f"""
        SELECT COUNT(*)
        FROM read_parquet('{OUTPUT_FILE.as_posix()}')
        """
    ).fetchone()[0]

    print()
    print(f"[OK] Output rows: {count:,}")
    print(f"[OK] Output file: {OUTPUT_FILE}")

    # ---------------------------------------------------------
    # Category counts
    # ---------------------------------------------------------

    print()
    print("Category distribution:")

    rows = con.execute(
        f"""
        SELECT
            category,
            COUNT(*) AS products
        FROM read_parquet('{OUTPUT_FILE.as_posix()}')
        GROUP BY category
        ORDER BY category
        """
    ).fetchall()

    for category, products in rows:
        print(f"  {category}: {products:,}")

    # ---------------------------------------------------------
    # Schema
    # ---------------------------------------------------------

    print()
    print("Output columns:")

    columns = con.execute(
        f"""
        DESCRIBE
        SELECT *
        FROM read_parquet('{OUTPUT_FILE.as_posix()}')
        """
    ).fetchall()

    for row in columns:
        print(f"  - {row[0]}")

    con.close()

    print()
    print("=" * 70)
    print("[SUCCESS] Geo-Gap product ground-truth dataset created.")
    print("=" * 70)


if __name__ == "__main__":
    main()