import duckdb

from app.ingestion.config import (
    DB_PATH,
    MIN_REVIEWS_FOR_RANKING,
    RECENCY_HALF_LIFE_DAYS,
)
from app.ingestion.merit_score import build_base_views, build_merit_table


con = duckdb.connect(str(DB_PATH))

print("[run_merit] Connected to persistent DuckDB database.")

tables = {
    row[0]
    for row in con.execute("SHOW TABLES").fetchall()
}

print("[run_merit] Existing tables:")
for table in sorted(tables):
    print(f"  - {table}")

required = {"product_dim", "brand_map", "product_brand"}

missing = required - tables

if missing:
    raise RuntimeError(
        "Required DuckDB tables are missing: "
        + ", ".join(sorted(missing))
    )

print("[run_merit] Required metadata/brand tables found.")

print("[run_merit] Building enriched review table...")
build_base_views(con)

print("[run_merit] Building product merit...")
build_merit_table(
    con,
    grain="product",
    half_life_days=RECENCY_HALF_LIFE_DAYS,
    min_reviews=MIN_REVIEWS_FOR_RANKING,
)

print("[run_merit] Building brand merit...")
build_merit_table(
    con,
    grain="brand",
    half_life_days=RECENCY_HALF_LIFE_DAYS,
    min_reviews=MIN_REVIEWS_FOR_RANKING,
)

print("\n[run_merit] Merit tables created successfully.")

print("\n=== MERIT TABLES ===")

for table in ["merit_product", "merit_brand"]:
    count = con.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    ranked = con.execute(
        f"SELECT COUNT(*) FROM {table} WHERE meets_min_reviews"
    ).fetchone()[0]

    print(
        f"{table}: {count:,} entities, "
        f"{ranked:,} ranked"
    )

con.close()

print("\n[run_merit] Done.")