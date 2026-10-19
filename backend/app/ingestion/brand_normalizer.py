"""
brand_normalizer.py  --  Clean + cluster the metadata `store` field (RapidFuzz)
==============================================================================
Doc requirement: "clean/normalize brand ('store') field" so that variants such as
"Anker" / "AnkerDirect" / "Anker Innovations" become ONE brand.

Input : product_dim(category, parent_asin, store, ...)   (from raw_meta_* files)
Output: table brand_map(category, store_raw, store_clean, brand_key,
                        brand_canonical, match_score, n_products)
        table product_brand(category, parent_asin, brand_canonical)

Method (deterministic, CPU-only, no model download):
  1. clean_store_name(): unicode-normalise, lower-case, strip marketing wrappers
     and corporate suffixes ("Inc", "Direct", "Official" ...), drop punctuation.
  2. Names that become identical after step 1 share one cluster automatically.
  3. Remaining distinct names are compared with rapidfuzz.fuzz.ratio inside a
     small "block" (same first 3 letters) so we never do an O(n^2) full compare.
     Most-frequent names are processed first and become the cluster's anchor.
  4. brand_canonical = the most frequent ORIGINAL spelling in the cluster.
Everything is written to brand_map so a human can audit every merge.

Known limitation: two spellings that differ in their first 3 letters are never
merged (that is the price of blocking). Review brand_map for such cases.
"""
"""
brand_normalizer.py
===================

Clean + cluster the metadata `store` field using deterministic
normalization and RapidFuzz.

Input:
    product_dim(
        category,
        parent_asin,
        store,
        ...
    )

Outputs:

    brand_map(
        category,
        store_raw,
        store_clean,
        brand_key,
        brand_canonical,
        match_score,
        n_products
    )

    product_brand(
        category,
        parent_asin,
        brand_canonical
    )

Method:
    1. Normalize Unicode and case.
    2. Remove known metadata wrappers/prefixes.
    3. Remove known safe suffixes such as "Inc", "LLC",
       "Company", "Store", "Direct", "Official".
    4. Preserve meaningful brand words such as "Shop".
    5. Normalize punctuation without unnecessarily splitting
       abbreviated brand names.
    6. Normalize common missing-value representations.
    7. Identical normalized keys automatically share a cluster.
    8. Remaining keys are compared using RapidFuzz inside
       a first-three-character block.
    9. More frequent keys become cluster anchors.
   10. The most frequent original spelling becomes the
       canonical brand name.
   11. Every raw-to-normalized-to-canonical mapping is stored
       in brand_map for auditability.

Important:
    This implementation is designed around the actual Amazon
    metadata values inspected during project validation.

Examples:

    Bath & Body Works
        -> bath and body works

    Bath and Body Works
        -> bath and body works

    e.l.f.
        -> elf

    M.A.C
        -> mac

    L.A. Girl
        -> la girl

    L'Oréal Paris
        -> loreal paris

    L’Oréal Paris
        -> loreal paris

    The Body Shop
        -> the body shop

    CoCo-Shop
        -> coco shop

    Unknown
        -> None

    N/A
        -> None

    AnkerDirect
        -> anker
"""

import re
import unicodedata
from collections import defaultdict
from typing import Optional

import duckdb
import pandas as pd
from rapidfuzz import fuzz, process

from .config import (
    BRAND_FUZZY_THRESHOLD,
    STORE_GLUED_SUFFIXES,
    STORE_MISSING_VALUES,
    STORE_PREFIX_PATTERNS,
    STORE_SUFFIX_PATTERNS,
    STORE_SUFFIX_WORDS,
)


# ---------------------------------------------------------------------------
# Additional normalized missing-value representations
# ---------------------------------------------------------------------------

NORMALIZED_MISSING_VALUES = {
    "",
    "none",
    "null",
    "na",
    "n a",
    "n/a",
    "nc",
    "n c",
    "n/c",
    "unknown",
    "nan",
}


# ---------------------------------------------------------------------------
# Helper: missing-value detection
# ---------------------------------------------------------------------------

def _is_missing_store_value(value: str) -> bool:
    """
    Determine whether a normalized store value represents missing data.

    This check is intentionally performed both before and after punctuation
    normalization because real metadata contains values such as:

        N/A
        "N/A"
        N\\A
        UNKNOWN
        NaN
    """

    if value is None:
        return True

    normalized = str(value).strip().lower()

    if normalized in STORE_MISSING_VALUES:
        return True

    if normalized in NORMALIZED_MISSING_VALUES:
        return True

    return False


# ---------------------------------------------------------------------------
# Brand/store cleaning
# ---------------------------------------------------------------------------

def clean_store_name(raw: Optional[str]) -> Optional[str]:
    """
    Return a normalized comparison key for a store/brand string.

    The function is deliberately conservative.

    It removes:
        - Unicode formatting differences
        - known metadata prefixes
        - known metadata suffixes
        - trademark/copyright symbols
        - punctuation that does not carry semantic meaning
        - apostrophes and hyphens where appropriate
        - excess whitespace
        - known corporate/retail suffixes
        - glued marketing suffixes such as AnkerDirect

    It preserves meaningful brand words.

    In particular:
        "The Body Shop" is NOT reduced to "the body".
        "CoCo-Shop" is NOT reduced to "coco".

    This is important because the real Amazon metadata audit showed
    that "Shop" can be part of a legitimate brand name.
    """

    # ------------------------------------------------------------------
    # 1. Handle Python/SQL NULL
    # ------------------------------------------------------------------

    if raw is None:
        return None

    # ------------------------------------------------------------------
    # 2. Convert to string and Unicode-normalize
    # ------------------------------------------------------------------

    s = unicodedata.normalize("NFKC", str(raw)).strip()

    if not s:
        return None

    # ------------------------------------------------------------------
    # 3. Early missing-value check
    # ------------------------------------------------------------------

    if _is_missing_store_value(s):
        return None

    # ------------------------------------------------------------------
    # 4. Remove configured metadata prefixes
    #
    # Examples:
    #   Visit the Anker
    #   Brand: Anker
    #   By Anker
    # ------------------------------------------------------------------

    for pattern in STORE_PREFIX_PATTERNS:
        s = re.sub(
            pattern,
            "",
            s,
            flags=re.IGNORECASE,
        ).strip()

    # ------------------------------------------------------------------
    # 5. Remove configured full suffix patterns
    #
    # Example:
    #   "Anker Store" -> "Anker"
    #
    # NOTE:
    #   We deliberately do NOT generically remove "Shop".
    # ------------------------------------------------------------------

    for pattern in STORE_SUFFIX_PATTERNS:
        s = re.sub(
            pattern,
            "",
            s,
            flags=re.IGNORECASE,
        ).strip()

    # ------------------------------------------------------------------
    # 6. Normalize ampersand
    #
    #   Bath & Body Works
    #       ->
    #   Bath and Body Works
    # ------------------------------------------------------------------

    s = s.replace("&", " and ")

    # ------------------------------------------------------------------
    # 7. Remove trademark/copyright symbols
    # ------------------------------------------------------------------

    s = re.sub(
        r"[®™©]",
        "",
        s,
    )

    # ------------------------------------------------------------------
    # 8. Normalize apostrophes and backticks
    #
    #   L'Oreal       -> LOreal
    #   L’Oréal       -> LOréal
    #   Burt's Bees   -> Burts Bees
    # ------------------------------------------------------------------

    s = re.sub(
        r"['’`]",
        "",
        s,
    )

    # ------------------------------------------------------------------
    # 9. Normalize hyphens
    #
    # Hyphens are usually formatting separators rather than part of the
    # identity used for matching.
    #
    #   L-Oreal       -> LOreal
    #   S-noilite     -> Snoilite
    #   M-BOX         -> MBOX
    #
    # However, spaces around hyphens are preserved naturally because
    # whitespace normalization occurs later.
    # ------------------------------------------------------------------

    s = re.sub(
        r"-",
        "",
        s,
    )

    # ------------------------------------------------------------------
    # 10. Remove remaining punctuation
    #
    # IMPORTANT:
    # Do NOT replace punctuation with spaces.
    #
    # This prevents:
    #
    #   e.l.f. -> e l f
    #   M.A.C  -> m a c
    #
    # Instead:
    #
    #   e.l.f. -> elf
    #   M.A.C  -> mac
    # ------------------------------------------------------------------

    s = re.sub(
        r"[^a-zA-Z0-9\s]",
        "",
        s,
    )

    # ------------------------------------------------------------------
    # 11. Lowercase and normalize whitespace
    # ------------------------------------------------------------------

    s = s.lower()

    s = re.sub(
        r"\s+",
        " ",
        s,
    ).strip()

    if not s:
        return None

    # ------------------------------------------------------------------
    # 12. Check missing values AGAIN after normalization
    #
    # This is important for:
    #
    #   "N/A"
    #   "N\\A"
    #   "\"N/A\""
    #   "UNKNOWN"
    #
    # which can become "na", "n a", etc.
    # ------------------------------------------------------------------

    if _is_missing_store_value(s):
        return None

    # ------------------------------------------------------------------
    # 13. Remove safe trailing corporate/retail words
    #
    # Examples:
    #
    #   "Anker Inc"       -> "anker"
    #   "Anker LLC"       -> "anker"
    #   "Anker Company"   -> "anker"
    #   "Anker Store"    -> "anker"
    #
    # "Shop" is intentionally not included here.
    # ------------------------------------------------------------------

    tokens = s.split()

    while (
        len(tokens) > 1
        and tokens[-1] in STORE_SUFFIX_WORDS
    ):
        tokens.pop()

    s = " ".join(tokens).strip()

    if not s:
        return None

    # ------------------------------------------------------------------
    # 14. Handle glued marketing suffixes
    #
    # Examples:
    #
    #   AnkerDirect
    #       -> anker
    #
    #   AnkerOfficial
    #       -> anker
    #
    # Only applies to single-token names.
    # ------------------------------------------------------------------

    if " " not in s:
        for suffix in STORE_GLUED_SUFFIXES:

            if (
                s.endswith(suffix)
                and len(s) - len(suffix) >= 3
            ):
                s = s[: -len(suffix)]
                break

    # ------------------------------------------------------------------
    # 15. Final missing-value check
    # ------------------------------------------------------------------

    if not s:
        return None

    if _is_missing_store_value(s):
        return None

    return s


# ---------------------------------------------------------------------------
# Blocking key
# ---------------------------------------------------------------------------

def _block_key(key: str) -> str:
    """
    Return the RapidFuzz comparison block.

    Spaces are ignored so that:

        "la girl"
        "lagirl"

    can belong to the same broad block.

    The first three characters are used to prevent an expensive
    all-vs-all comparison across every brand.
    """

    return key.replace(" ", "")[:3]


# ---------------------------------------------------------------------------
# Build brand map
# ---------------------------------------------------------------------------

def build_brand_map(
    store_counts: pd.DataFrame,
    threshold: int = BRAND_FUZZY_THRESHOLD,
) -> pd.DataFrame:
    """
    Build the deterministic brand clustering/audit table.

    Parameters
    ----------
    store_counts:
        DataFrame containing:

            store_raw
            n_products

        One row per raw store value.

    threshold:
        RapidFuzz similarity threshold.

    Returns
    -------
    pd.DataFrame
        One row per usable raw store value containing:

            store_raw
            store_clean
            brand_key
            brand_canonical
            match_score
            n_products
    """

    if store_counts.empty:
        return pd.DataFrame(
            columns=[
                "store_raw",
                "store_clean",
                "brand_key",
                "brand_canonical",
                "match_score",
                "n_products",
            ]
        )

    df = store_counts.copy()

    # ---------------------------------------------------------------
    # Validate expected columns
    # ---------------------------------------------------------------

    required_columns = {
        "store_raw",
        "n_products",
    }

    missing_columns = required_columns - set(df.columns)

    if missing_columns:
        raise ValueError(
            "store_counts is missing required columns: "
            + ", ".join(sorted(missing_columns))
        )

    # ---------------------------------------------------------------
    # Normalize raw store names
    # ---------------------------------------------------------------

    df["store_clean"] = df["store_raw"].map(
        clean_store_name
    )

    # Remove unusable/missing store values
    df = df[
        df["store_clean"].notna()
    ].copy()

    if df.empty:
        return pd.DataFrame(
            columns=[
                "store_raw",
                "store_clean",
                "brand_key",
                "brand_canonical",
                "match_score",
                "n_products",
            ]
        )

    # ---------------------------------------------------------------
    # Aggregate product weight by normalized key
    #
    # If:
    #
    #   Bath & Body Works
    #   Bath and Body Works
    #
    # both become:
    #
    #   bath and body works
    #
    # they naturally receive one combined weight.
    # ---------------------------------------------------------------

    key_weight = (
        df.groupby("store_clean")["n_products"]
        .sum()
        .sort_values(ascending=False)
    )

    # ---------------------------------------------------------------
    # RapidFuzz clustering
    #
    # Most frequent normalized names are processed first.
    # The first unmatched name becomes the anchor.
    # ---------------------------------------------------------------

    anchors_by_block = defaultdict(list)

    key_to_anchor = {}
    key_to_score = {}

    for key in key_weight.index:

        block = anchors_by_block[
            _block_key(key)
        ]

        # -----------------------------------------------------------
        # Search only inside the corresponding block.
        # -----------------------------------------------------------

        if block:
            hit = process.extractOne(
                key,
                block,
                scorer=fuzz.ratio,
                score_cutoff=threshold,
            )
        else:
            hit = None

        # -----------------------------------------------------------
        # Existing sufficiently similar anchor
        # -----------------------------------------------------------

        if hit:
            matched_anchor = hit[0]
            score = float(hit[1])

            key_to_anchor[key] = matched_anchor
            key_to_score[key] = score

        # -----------------------------------------------------------
        # New brand anchor
        # -----------------------------------------------------------

        else:
            block.append(key)

            key_to_anchor[key] = key
            key_to_score[key] = 100.0

    # ---------------------------------------------------------------
    # Assign cluster information
    # ---------------------------------------------------------------

    df["brand_key"] = df["store_clean"].map(
        key_to_anchor
    )

    df["match_score"] = df["store_clean"].map(
        key_to_score
    )

    # ---------------------------------------------------------------
    # Select canonical spelling
    #
    # The original spelling with the highest product count inside
    # each cluster becomes the canonical display name.
    # ---------------------------------------------------------------

    top_raw = (
        df.sort_values(
            "n_products",
            ascending=False,
        )
        .drop_duplicates(
            "brand_key"
        )
        .set_index("brand_key")["store_raw"]
    )

    df["brand_canonical"] = df["brand_key"].map(
        top_raw
    )

    # ---------------------------------------------------------------
    # Return audit columns in deterministic order
    # ---------------------------------------------------------------

    return df[
        [
            "store_raw",
            "store_clean",
            "brand_key",
            "brand_canonical",
            "match_score",
            "n_products",
        ]
    ]


# ---------------------------------------------------------------------------
# Profile raw store values
# ---------------------------------------------------------------------------

def profile_store_values(
    con: duckdb.DuckDBPyConnection,
    category: str,
    top: int = 50,
) -> pd.DataFrame:
    """
    Return the most frequent raw store values for a category.

    This function is intended for dataset inspection before
    changing normalization rules.
    """

    return con.execute(
        """
        SELECT
            store AS store_raw,
            COUNT(*) AS n_products
        FROM product_dim
        WHERE category = ?
        GROUP BY store
        ORDER BY n_products DESC
        LIMIT ?
        """,
        [category, top],
    ).df()


# ---------------------------------------------------------------------------
# Normalize brands inside DuckDB
# ---------------------------------------------------------------------------

def normalize_brands(
    con: duckdb.DuckDBPyConnection,
    category: str,
) -> bool:
    """
    Build brand_map and product_brand for one category.

    brand_map:
        One audit row per usable raw store value.

    product_brand:
        One row per product having a usable store/brand mapping.
    """

    # ---------------------------------------------------------------
    # Verify product_dim exists
    # ---------------------------------------------------------------

    tables = {
        row[0]
        for row in con.execute(
            "SHOW TABLES"
        ).fetchall()
    }

    if "product_dim" not in tables:
        print(
            "[brand_normalizer] product_dim table not found."
        )
        return False

    # ---------------------------------------------------------------
    # Extract raw store counts
    #
    # IMPORTANT:
    # RapidFuzz operates on DISTINCT raw store values here,
    # not on every product row.
    # ---------------------------------------------------------------

    counts = con.execute(
        """
        SELECT
            store AS store_raw,
            COUNT(*) AS n_products
        FROM product_dim
        WHERE category = ?
          AND store IS NOT NULL
        GROUP BY store
        """,
        [category],
    ).df()

    if counts.empty:
        print(
            f"[brand_normalizer] {category}: "
            "no non-null store values found."
        )
        return False

    # ---------------------------------------------------------------
    # Build brand map in Python
    # ---------------------------------------------------------------

    brand_map = build_brand_map(
        counts,
        threshold=BRAND_FUZZY_THRESHOLD,
    )

    if brand_map.empty:
        print(
            f"[brand_normalizer] {category}: "
            "no usable brand values after normalization."
        )
        return False

    brand_map.insert(
        0,
        "category",
        category,
    )

    # ---------------------------------------------------------------
    # Create audit table
    # ---------------------------------------------------------------

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS brand_map (
            category VARCHAR,
            store_raw VARCHAR,
            store_clean VARCHAR,
            brand_key VARCHAR,
            brand_canonical VARCHAR,
            match_score DOUBLE,
            n_products BIGINT
        )
        """
    )

    # Replace only this category.
    con.execute(
        """
        DELETE FROM brand_map
        WHERE category = ?
        """,
        [category],
    )

    # Register pandas DataFrame temporarily.
    con.register(
        "_brand_map_df",
        brand_map,
    )

    try:
        con.execute(
            """
            INSERT INTO brand_map
            SELECT
                category,
                store_raw,
                store_clean,
                brand_key,
                brand_canonical,
                match_score,
                n_products
            FROM _brand_map_df
            """
        )
    finally:
        con.unregister(
            "_brand_map_df"
        )

    # ---------------------------------------------------------------
    # Create product -> brand table
    # ---------------------------------------------------------------

    con.execute(
        """
        CREATE TABLE IF NOT EXISTS product_brand (
            category VARCHAR,
            parent_asin VARCHAR,
            brand_canonical VARCHAR
        )
        """
    )

    # Replace only this category.
    con.execute(
        """
        DELETE FROM product_brand
        WHERE category = ?
        """,
        [category],
    )

    # ---------------------------------------------------------------
    # Join product_dim to brand_map
    #
    # Missing/invalid stores intentionally do not receive a
    # product_brand row.
    # ---------------------------------------------------------------

    con.execute(
        """
        INSERT INTO product_brand
        SELECT
            p.category,
            p.parent_asin,
            b.brand_canonical
        FROM product_dim AS p
        INNER JOIN brand_map AS b
            ON b.category = p.category
           AND b.store_raw = p.store
        WHERE p.category = ?
        """,
        [category],
    )

    # ---------------------------------------------------------------
    # Reporting
    # ---------------------------------------------------------------

    n_raw = int(
        brand_map["store_raw"].nunique()
    )

    n_clean = int(
        brand_map["store_clean"].nunique()
    )

    n_brand = int(
        brand_map["brand_canonical"].nunique()
    )

    n_products_mapped = con.execute(
        """
        SELECT COUNT(*)
        FROM product_brand
        WHERE category = ?
        """,
        [category],
    ).fetchone()[0]

    print(
        f"[brand_normalizer] {category}: "
        f"{n_raw:,} raw store names -> "
        f"{n_clean:,} normalized keys -> "
        f"{n_brand:,} brands"
    )

    print(
        f"[brand_normalizer] {category}: "
        f"{n_products_mapped:,} products mapped to brands"
    )

    return True