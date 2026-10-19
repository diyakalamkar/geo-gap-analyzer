import duckdb

from app.ingestion.config import (
    DB_PATH,
    LEADERBOARD_TOP_N,
    MOMENTUM_WINDOW_DAYS,
)
from app.ingestion.leaderboards_and_trends import (
    build_leaderboards,
    build_trend_views,
    export_handoff_files,
)


con = duckdb.connect(str(DB_PATH))

print("[run_leaderboards] Connected to persistent DuckDB database.")

print("[run_leaderboards] Building product and brand leaderboards...")
build_leaderboards(
    con,
    top_n=LEADERBOARD_TOP_N,
)

print("[run_leaderboards] Building monthly, quarterly and momentum trends...")
build_trend_views(
    con,
    window_days=MOMENTUM_WINDOW_DAYS,
)

print("[run_leaderboards] Exporting handoff files...")
export_handoff_files(con)

print("\n=== OUTPUT TABLE COUNTS ===")

tables = [
    "leaderboard_product",
    "leaderboard_brand",
    "trend_category_monthly",
    "trend_entity_quarterly",
    "recency_momentum_product",
]

for table in tables:
    count = con.execute(
        f"SELECT COUNT(*) FROM {table}"
    ).fetchone()[0]

    print(f"{table}: {count:,} rows")

con.close()

print("\n[run_leaderboards] Done.")