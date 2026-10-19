from pathlib import Path
import json
import duckdb

from app.ingestion.config import DB_PATH, EXPORT_DIR


OUTPUT_FILE = EXPORT_DIR / "person1_handoff_summary.json"


def main():
    con = duckdb.connect(str(DB_PATH))

    summary = {
        "pipeline": "Geo-Gap Analyzer — Person 1 Ground-Truth Merit Engine",
        "status": "completed",
        "categories": [],
        "tables": {},
        "exports": {},
    }

    # ---------------------------------------------------------
    # Categories
    # ---------------------------------------------------------

    categories = [
        row[0]
        for row in con.execute(
            "SELECT DISTINCT category FROM product_dim ORDER BY category"
        ).fetchall()
    ]

    summary["categories"] = categories

    # ---------------------------------------------------------
    # Table counts
    # ---------------------------------------------------------

    tables = [
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

    for table in tables:
        count = con.execute(
            f"SELECT COUNT(*) FROM {table}"
        ).fetchone()[0]

        summary["tables"][table] = {
            "rows": count
        }

    # ---------------------------------------------------------
    # Merit statistics
    # ---------------------------------------------------------

    summary["merit"] = {
        "product": {},
        "brand": {},
    }

    for category in categories:

        product_row = con.execute(
            """
            SELECT
                COUNT(*) AS total_entities,
                COUNT(*) FILTER (
                    WHERE meets_min_reviews
                ) AS ranked_entities
            FROM merit_product
            WHERE category = ?
            """,
            [category],
        ).fetchone()

        brand_row = con.execute(
            """
            SELECT
                COUNT(*) AS total_entities,
                COUNT(*) FILTER (
                    WHERE meets_min_reviews
                ) AS ranked_entities
            FROM merit_brand
            WHERE category = ?
            """,
            [category],
        ).fetchone()

        summary["merit"]["product"][category] = {
            "total_entities": product_row[0],
            "ranked_entities": product_row[1],
        }

        summary["merit"]["brand"][category] = {
            "total_entities": brand_row[0],
            "ranked_entities": brand_row[1],
        }

    # ---------------------------------------------------------
    # Export files
    # ---------------------------------------------------------

    expected_exports = [
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

    for filename in expected_exports:
        path = EXPORT_DIR / filename

        summary["exports"][filename] = {
            "exists": path.exists(),
            "size_bytes": path.stat().st_size if path.exists() else 0,
        }

    con.close()

    # ---------------------------------------------------------
    # Write JSON
    # ---------------------------------------------------------

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("=" * 70)
    print("PERSON 1 HANDOFF SUMMARY")
    print("=" * 70)
    print(f"Output: {OUTPUT_FILE}")
    print(f"Categories: {', '.join(categories)}")
    print()

    print("Tables:")
    for table, info in summary["tables"].items():
        print(f"  {table:<32} {info['rows']:>12,} rows")

    print()
    print("Export files:")
    for filename, info in summary["exports"].items():
        status = "OK" if info["exists"] else "MISSING"
        print(f"  [{status}] {filename}")

    print()
    print("[SUCCESS] Person-1 (Anuya) handoff summary created.")

if __name__ == "__main__":
    main()