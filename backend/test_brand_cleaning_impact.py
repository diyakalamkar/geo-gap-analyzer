from app.ingestion.duckdb_pipeline import get_connection
from app.ingestion.brand_normalizer import clean_store_name


def main():
    con = get_connection()

    categories = [
        "All_Beauty",
        "Beauty_and_Personal_Care",
    ]

    for category in categories:
        print("\n" + "=" * 80)
        print(f"CATEGORY: {category}")
        print("=" * 80)

        df = con.execute(
            """
            SELECT
                store AS store_raw,
                COUNT(*) AS n_products
            FROM product_dim
            WHERE category = ?
              AND store IS NOT NULL
            GROUP BY store
            ORDER BY n_products DESC
            """,
            [category],
        ).fetchdf()

        print(f"Distinct non-null store names: {len(df):,}")

        # Apply current normalization
        df["store_clean"] = df["store_raw"].apply(clean_store_name)

        # ------------------------------------------------------------
        # 1. Values containing "shop"
        # ------------------------------------------------------------
        shop_df = df[
            df["store_raw"]
            .astype(str)
            .str.lower()
            .str.contains("shop", regex=False)
        ].copy()

        print("\n--- STORE NAMES CONTAINING 'SHOP' ---")
        print(f"Count: {len(shop_df):,}")

        if not shop_df.empty:
            print(
                shop_df[
                    ["store_raw", "store_clean", "n_products"]
                ].head(50).to_string(index=False)
            )

        # ------------------------------------------------------------
        # 2. Values where normalization removes/reduces information
        # ------------------------------------------------------------
        changed_df = df[
            df["store_clean"].notna()
            & (
                df["store_raw"].astype(str).str.lower()
                != df["store_clean"]
            )
        ].copy()

        print("\n--- EXAMPLES WHERE CLEANING CHANGES THE NAME ---")
        print(f"Count: {len(changed_df):,}")

        if not changed_df.empty:
            print(
                changed_df[
                    ["store_raw", "store_clean", "n_products"]
                ].head(100).to_string(index=False)
            )

        # ------------------------------------------------------------
        # 3. Names containing dots
        # ------------------------------------------------------------
        dot_df = df[
            df["store_raw"]
            .astype(str)
            .str.contains(".", regex=False)
        ].copy()

        print("\n--- STORE NAMES CONTAINING '.' ---")
        print(f"Count: {len(dot_df):,}")

        if not dot_df.empty:
            print(
                dot_df[
                    ["store_raw", "store_clean", "n_products"]
                ].head(50).to_string(index=False)
            )

        # ------------------------------------------------------------
        # 4. Names becoming very short
        # ------------------------------------------------------------
        short_df = df[
            df["store_clean"].notna()
            & (df["store_clean"].str.len() <= 4)
        ].copy()

        print("\n--- VERY SHORT CLEANED BRAND NAMES (<= 4 chars) ---")
        print(f"Count: {len(short_df):,}")

        if not short_df.empty:
            print(
                short_df[
                    ["store_raw", "store_clean", "n_products"]
                ].head(100).to_string(index=False)
            )

    con.close()


if __name__ == "__main__":
    main()