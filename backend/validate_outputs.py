from pathlib import Path
import duckdb

from app.ingestion.config import DB_PATH, EXPORT_DIR

EXPECTED_TABLES = [
    "product_dim",
    "brand_map",
    "product_brand",
    "reviews_enriched",
    "category_ref_date",
    "merit_product",
    "merit_brand",
    "leaderboard_product",
    "leaderboard_brand",
    "trend_category_monthly",
    "trend_entity_quarterly",
    "recency_momentum_product",
]

EXPECTED_EXPORTS = [
    "merit_product.parquet",
    "merit_brand.parquet",
    "leaderboard_product.parquet",
    "leaderboard_brand.parquet",
    "trend_category_monthly.parquet",
    "trend_entity_quarterly.parquet",
    "recency_momentum_product.parquet",
    "brand_map.parquet",
    "product_brand.parquet",
    "product_dim.parquet",
]

print("=" * 70)
print("GEO-GAP ANALYZER — FINAL OUTPUT VALIDATION")
print("=" * 70)

print(f"\nDuckDB database:")
print(DB_PATH)

print(f"\nExport directory:")
print(EXPORT_DIR)

con = duckdb.connect(str(DB_PATH))

# ------------------------------------------------------------
# 1. DuckDB tables
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("1. DUCKDB TABLE VALIDATION")
print("=" * 70)

tables = {
    row[0]
    for row in con.execute("SHOW TABLES").fetchall()
}

for table in EXPECTED_TABLES:
    if table in tables:
        count = con.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        print(f"[OK] {table:<30} {count:>12,} rows")
    else:
        print(f"[MISSING] {table}")

# ------------------------------------------------------------
# 2. Export files
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("2. EXPORTED FILE VALIDATION")
print("=" * 70)

for filename in EXPECTED_EXPORTS:
    path = EXPORT_DIR / filename

    if path.exists():
        size_mb = path.stat().st_size / (1024 * 1024)

        print(
            f"[OK] {filename:<38} "
            f"{size_mb:>10.2f} MB"
        )
    else:
        print(f"[MISSING] {filename}")

# ------------------------------------------------------------
# 3. Category-level merit validation
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("3. MERIT VALIDATION BY CATEGORY")
print("=" * 70)

query = """
SELECT
    category,
    COUNT(*) AS total_products,
    COUNT(*) FILTER (WHERE meets_min_reviews) AS ranked_products,
    MIN(merit_score) FILTER (WHERE meets_min_reviews) AS min_score,
    MAX(merit_score) FILTER (WHERE meets_min_reviews) AS max_score
FROM merit_product
GROUP BY category
ORDER BY category
"""

for row in con.execute(query).fetchall():
    category, total, ranked, min_score, max_score = row

    print(f"\nCategory: {category}")
    print(f"  Total products : {total:,}")
    print(f"  Ranked products: {ranked:,}")
    print(f"  Merit min      : {min_score}")
    print(f"  Merit max      : {max_score}")

# ------------------------------------------------------------
# 4. Brand-level merit validation
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("4. BRAND MERIT VALIDATION BY CATEGORY")
print("=" * 70)

query = """
SELECT
    category,
    COUNT(*) AS total_brands,
    COUNT(*) FILTER (WHERE meets_min_reviews) AS ranked_brands,
    MIN(merit_score) FILTER (WHERE meets_min_reviews) AS min_score,
    MAX(merit_score) FILTER (WHERE meets_min_reviews) AS max_score
FROM merit_brand
GROUP BY category
ORDER BY category
"""

for row in con.execute(query).fetchall():
    category, total, ranked, min_score, max_score = row

    print(f"\nCategory: {category}")
    print(f"  Total brands  : {total:,}")
    print(f"  Ranked brands : {ranked:,}")
    print(f"  Merit min     : {min_score}")
    print(f"  Merit max     : {max_score}")

# ------------------------------------------------------------
# 5. Leaderboard validation
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("5. LEADERBOARD VALIDATION")
print("=" * 70)

for table in ["leaderboard_product", "leaderboard_brand"]:

    query = f"""
    SELECT
        category,
        COUNT(*) AS rows,
        MIN(rank) AS min_rank,
        MAX(rank) AS max_rank
    FROM {table}
    GROUP BY category
    ORDER BY category
    """

    print(f"\n{table}")

    for row in con.execute(query).fetchall():
        category, rows, min_rank, max_rank = row

        print(
            f"  {category}: "
            f"{rows:,} rows, "
            f"rank {min_rank}–{max_rank}"
        )

# ------------------------------------------------------------
# 6. Trend validation
# ------------------------------------------------------------

print("\n" + "=" * 70)
print("6. TREND VALIDATION")
print("=" * 70)

for table in [
    "trend_category_monthly",
    "trend_entity_quarterly",
    "recency_momentum_product",
]:

    count = con.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    print(f"[OK] {table:<30} {count:>12,} rows")

# ------------------------------------------------------------
# 7. Final status
# ------------------------------------------------------------

missing_tables = [
    table for table in EXPECTED_TABLES
    if table not in tables
]

missing_exports = [
    filename
    for filename in EXPECTED_EXPORTS
    if not (EXPORT_DIR / filename).exists()
]

print("\n" + "=" * 70)
print("FINAL STATUS")
print("=" * 70)

if not missing_tables and not missing_exports:
    print("[SUCCESS] All expected tables and export files are present.")
else:
    print("[CHECK REQUIRED] Some expected outputs are missing.")

    if missing_tables:
        print("\nMissing tables:")
        for table in missing_tables:
            print(f"  - {table}")

    if missing_exports:
        print("\nMissing exports:")
        for filename in missing_exports:
            print(f"  - {filename}")

con.close()

print("\nValidation complete.")
