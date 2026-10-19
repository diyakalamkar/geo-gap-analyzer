from pathlib import Path
import pandas as pd

from app.geo_gap.response_store import load_responses
from app.geo_gap.brand_extractor import extract_brands_from_response


PROJECT_ROOT = Path(__file__).resolve().parents[3]

EXPORT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "exports"
)

PRODUCT_MENTIONS_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "geo_gap_product_mentions.parquet"
)

GROUND_TRUTH_PATH = (
    EXPORT_DIR
    / "geo_gap_product_ground_truth.parquet"
)

BRAND_OUTPUT_PATH = (
    EXPORT_DIR
    / "llm_brand_mentions.parquet"
)

PRODUCT_VISIBILITY_PATH = (
    EXPORT_DIR
    / "product_visibility.parquet"
)

BRAND_VISIBILITY_PATH = (
    EXPORT_DIR
    / "brand_visibility.parquet"
)

PRODUCT_GAP_PATH = (
    EXPORT_DIR
    / "geo_gap_product.parquet"
)

BRAND_GAP_PATH = (
    EXPORT_DIR
    / "geo_gap_brand.parquet"
)


def build_brand_mentions():
    responses = load_responses("beauty_products_groq.jsonl")

    rows = []

    for response in responses:
        brands = extract_brands_from_response(
            response["query_id"],
            response["response_text"],
        )

        for brand in brands:
            rows.append(
                {
                    "query_id": brand["query_id"],
                    "position": brand["position"],
                    "llm_brand_name": brand["brand_name"],
                }
            )

    return pd.DataFrame(rows)


def build_product_visibility(product_mentions):
    total_queries = product_mentions["query_id"].nunique()

    matched = product_mentions[
        product_mentions["matched"]
    ].copy()

    if matched.empty:
        return pd.DataFrame(
            columns=[
                "parent_asin",
                "mention_count",
                "query_coverage",
                "mean_position",
                "visibility_score",
            ]
        )

    visibility = (
        matched.groupby("matched_parent_asin")
        .agg(
            mention_count=("matched_parent_asin", "size"),
            query_coverage=("query_id", "nunique"),
            mean_position=("position", "mean"),
        )
        .reset_index()
        .rename(
            columns={
                "matched_parent_asin": "parent_asin"
            }
        )
    )

    visibility["query_coverage"] = (
        visibility["query_coverage"] / total_queries
    )

    visibility["visibility_score"] = (
        visibility["mention_count"]
        * visibility["query_coverage"]
        / visibility["mean_position"]
    )

    return visibility


def build_brand_visibility(brand_mentions):
    total_queries = brand_mentions["query_id"].nunique()

    if brand_mentions.empty:
        return pd.DataFrame(
            columns=[
                "llm_brand_name",
                "mention_count",
                "query_coverage",
                "mean_position",
                "visibility_score",
            ]
        )

    visibility = (
        brand_mentions.groupby("llm_brand_name")
        .agg(
            mention_count=("llm_brand_name", "size"),
            query_coverage=("query_id", "nunique"),
            mean_position=("position", "mean"),
        )
        .reset_index()
    )

    visibility["query_coverage"] = (
        visibility["query_coverage"] / total_queries
    )

    visibility["visibility_score"] = (
        visibility["mention_count"]
        * visibility["query_coverage"]
        / visibility["mean_position"]
    )

    return visibility


def build_product_gap(product_visibility, ground_truth):
    truth = ground_truth[
        [
            "parent_asin",
            "category",
            "product_title",
            "store",
            "ground_truth_rank",
            "ground_truth_merit_score",
        ]
    ].drop_duplicates("parent_asin")

    result = truth.merge(
        product_visibility,
        on="parent_asin",
        how="left",
    )

    result["mention_count"] = (
        result["mention_count"].fillna(0).astype(int)
    )

    result["query_coverage"] = (
        result["query_coverage"].fillna(0)
    )

    result["mean_position"] = (
        result["mean_position"]
    )

    result["visibility_score"] = (
        result["visibility_score"].fillna(0)
    )

    result["geo_gap"] = (
        result["ground_truth_merit_score"]
        - result["visibility_score"]
    )

    result["visibility_status"] = "not_mentioned"

    mentioned = result["mention_count"] > 0

    result.loc[
        mentioned,
        "visibility_status"
    ] = "mentioned"

    high_merit = (
        result["ground_truth_merit_score"]
        >= result["ground_truth_merit_score"].quantile(0.75)
    )

    high_visibility = (
        result["visibility_score"]
        >= result["visibility_score"].quantile(0.75)
    )

    result.loc[
        high_merit & ~high_visibility,
        "visibility_status"
    ] = "high_merit_low_visibility"

    result.loc[
        high_merit & high_visibility,
        "visibility_status"
    ] = "high_merit_high_visibility"

    return result


def build_brand_gap(brand_visibility, ground_truth):
    brand_truth = (
        ground_truth[
            ["store", "ground_truth_merit_score"]
        ]
        .dropna(subset=["store"])
        .groupby("store")
        .agg(
            ground_truth_merit_score=(
                "ground_truth_merit_score",
                "mean",
            )
        )
        .reset_index()
        .rename(columns={"store": "ground_truth_brand_name"})
    )

    result = brand_truth.merge(
        brand_visibility,
        left_on="ground_truth_brand_name",
        right_on="llm_brand_name",
        how="left",
    )

    result["mention_count"] = (
        result["mention_count"].fillna(0).astype(int)
    )

    result["query_coverage"] = (
        result["query_coverage"].fillna(0)
    )

    result["visibility_score"] = (
        result["visibility_score"].fillna(0)
    )

    result["geo_gap"] = (
        result["ground_truth_merit_score"]
        - result["visibility_score"]
    )

    return result


def main():
    EXPORT_DIR.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("FINAL GEO-GAP METRICS")
    print("=" * 80)

    print("\n1. Loading product mentions...")
    product_mentions = pd.read_parquet(
        PRODUCT_MENTIONS_PATH
    )

    print(f"Product mentions: {len(product_mentions):,}")
    print(
        f"Matched product mentions: "
        f"{int(product_mentions['matched'].sum()):,}"
    )
    print(
        f"Unmatched product mentions: "
        f"{int((~product_mentions['matched']).sum()):,}"
    )

    print("\n2. Building brand mentions...")
    brand_mentions = build_brand_mentions()

    print(f"Brand mentions: {len(brand_mentions):,}")

    brand_mentions.to_parquet(
        BRAND_OUTPUT_PATH,
        index=False,
    )

    print(f"Saved: {BRAND_OUTPUT_PATH}")

    print("\n3. Building product visibility...")
    product_visibility = build_product_visibility(
        product_mentions
    )

    product_visibility.to_parquet(
        PRODUCT_VISIBILITY_PATH,
        index=False,
    )

    print(
        f"Products with LLM visibility: "
        f"{len(product_visibility):,}"
    )

    print(f"Saved: {PRODUCT_VISIBILITY_PATH}")

    print("\n4. Building brand visibility...")
    brand_visibility = build_brand_visibility(
        brand_mentions
    )

    brand_visibility.to_parquet(
        BRAND_VISIBILITY_PATH,
        index=False,
    )

    print(
        f"Brands with LLM visibility: "
        f"{len(brand_visibility):,}"
    )

    print(f"Saved: {BRAND_VISIBILITY_PATH}")

    print("\n5. Loading ground truth...")
    ground_truth = pd.read_parquet(
        GROUND_TRUTH_PATH,
        columns=[
            "category",
            "parent_asin",
            "product_title",
            "store",
            "ground_truth_rank",
            "ground_truth_merit_score",
        ],
    )

    print(
        f"Ground-truth rows: "
        f"{len(ground_truth):,}"
    )

    print("\n6. Building product Geo-Gap...")
    product_gap = build_product_gap(
        product_visibility,
        ground_truth,
    )

    product_gap.to_parquet(
        PRODUCT_GAP_PATH,
        index=False,
    )

    print(
        f"Product Geo-Gap rows: "
        f"{len(product_gap):,}"
    )

    print(f"Saved: {PRODUCT_GAP_PATH}")

    print("\n7. Building brand Geo-Gap...")
    brand_gap = build_brand_gap(
        brand_visibility,
        ground_truth,
    )

    brand_gap.to_parquet(
        BRAND_GAP_PATH,
        index=False,
    )

    print(
        f"Brand Geo-Gap rows: "
        f"{len(brand_gap):,}"
    )

    print(f"Saved: {BRAND_GAP_PATH}")

    print("\n" + "=" * 80)
    print("FINAL OUTPUT SUMMARY")
    print("=" * 80)

    print(
        f"LLM product mentions: "
        f"{len(product_mentions):,}"
    )

    print(
        f"LLM brand mentions: "
        f"{len(brand_mentions):,}"
    )

    print(
        f"Product visibility entities: "
        f"{len(product_visibility):,}"
    )

    print(
        f"Brand visibility entities: "
        f"{len(brand_visibility):,}"
    )

    print(
        f"Product Geo-Gap rows: "
        f"{len(product_gap):,}"
    )

    print(
        f"Brand Geo-Gap rows: "
        f"{len(brand_gap):,}"
    )

    print("\nYOUR PERSON 1 DATA OUTPUT IS COMPLETE.")


if __name__ == "__main__":
    main()