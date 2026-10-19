from app.ingestion.duckdb_pipeline import get_connection

con = get_connection()

result = con.execute("""
    SELECT
        category,
        store_raw,
        store_clean,
        brand_canonical,
        match_score,
        n_products
    FROM brand_map
    WHERE category = 'All_Beauty'
    ORDER BY n_products DESC
    LIMIT 30
""").df()

print(result.to_string(index=False))

con.close()