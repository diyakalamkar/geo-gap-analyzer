from app.ingestion.duckdb_pipeline import get_connection

con = get_connection()

query = """
SELECT
    category,
    COUNT(*) AS products,
    COUNT(DISTINCT parent_asin) AS unique_parent_asin,
    COUNT(*) FILTER (
        WHERE store IS NOT NULL
        AND TRIM(store) != ''
    ) AS with_store
FROM product_dim
GROUP BY category
ORDER BY category
"""

result = con.execute(query).fetchdf()

print(result.to_string(index=False))

con.close()