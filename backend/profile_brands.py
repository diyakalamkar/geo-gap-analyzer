from app.ingestion.duckdb_pipeline import get_connection
from app.ingestion.brand_normalizer import profile_store_values

con = get_connection()

for category in [
    "All_Beauty",
    "Beauty_and_Personal_Care",
]:
    print("\n" + "=" * 80)
    print(category)
    print("=" * 80)

    df = profile_store_values(con, category, top=50)

    print(df.to_string(index=False))

con.close()