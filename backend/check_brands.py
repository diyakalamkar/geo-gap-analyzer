from app.ingestion.duckdb_pipeline import get_connection

con = get_connection()

print("\n=== BRAND MAP ===")

brand_map = con.execute("""
    SELECT
        category,
        COUNT(*) AS mapping_rows,
        COUNT(DISTINCT store_raw) AS raw_store_names,
        COUNT(DISTINCT brand_canonical) AS brands
    FROM brand_map
    GROUP BY category
    ORDER BY category
""").df()

print(brand_map.to_string(index=False))

print("\n=== PRODUCT BRAND ===")

product_brand = con.execute("""
    SELECT
        category,
        COUNT(*) AS product_brand_rows,
        COUNT(DISTINCT parent_asin) AS products,
        COUNT(DISTINCT brand_canonical) AS brands
    FROM product_brand
    GROUP BY category
    ORDER BY category
""").df()

print(product_brand.to_string(index=False))

print("\n=== DUPLICATE PRODUCT-BRAND MAPPINGS ===")

duplicates = con.execute("""
    SELECT
        category,
        parent_asin,
        COUNT(*) AS mapping_count
    FROM product_brand
    GROUP BY category, parent_asin
    HAVING COUNT(*) > 1
    ORDER BY category, parent_asin
    LIMIT 20
""").df()

if duplicates.empty:
    print("No duplicate product-brand mappings found.")
else:
    print(duplicates.to_string(index=False))

con.close()