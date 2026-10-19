from pathlib import Path

import pandas as pd

from app.geo_gap.brand_extractor import extract_brands_from_response
from app.geo_gap.name_normalizer import normalize_name
from app.geo_gap.response_store import load_responses


PROJECT_ROOT = Path(__file__).resolve().parents[3]

GROUND_TRUTH_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "exports"
    / "geo_gap_product_ground_truth.parquet"
)


def load_brand_ground_truth() -> pd.DataFrame:
    return pd.read_parquet(
        GROUND_TRUTH_PATH,
        columns=[
            "category",
            "store",
            "ground_truth_merit_score",
        ],
    )


def build_brand_lookup(
    ground_truth: pd.DataFrame,
) -> dict:

    brand_rows = (
        ground_truth[
            ground_truth["store"].notna()
        ][
            [
                "store",
            ]
        ]
        .drop_duplicates()
        .copy()
    )

    brand_rows["normalized_name"] = (
        brand_rows["store"]
        .map(normalize_name)
    )

    brand_rows = brand_rows[
        brand_rows["normalized_name"] != ""
    ]

    grouped = (
        brand_rows
        .groupby("normalized_name")["store"]
        .agg(list)
    )

    lookup = {}

    for normalized_name, stores in grouped.items():

        unique_stores = list(
            dict.fromkeys(stores)
        )

        if unique_stores:
            lookup[normalized_name] = unique_stores[0]
    return lookup


# Explicit aliases for verified brand-name variants.
# Keys and values are normalized using normalize_name().
BRAND_ALIASES = {
    "mac cosmetics": "mac",
    "dior beauty": "dior",
}


def match_brand(
    brand_name: str,
    lookup: dict,
):
    normalized_name = normalize_name(brand_name)

    if not normalized_name:
        return None

    # Try an exact match first.
    matched_store = lookup.get(normalized_name)

    if matched_store is not None:
        return matched_store

    # Try an explicitly configured alias.
    canonical_name = BRAND_ALIASES.get(normalized_name)

    if canonical_name is not None:
        return lookup.get(canonical_name)

    return None


if __name__ == "__main__":

    print(
        "Loading brand ground truth..."
    )

    ground_truth = load_brand_ground_truth()

    print(
        f"Ground-truth rows: "
        f"{len(ground_truth):,}"
    )

    lookup = build_brand_lookup(
        ground_truth
    )

    print(
        f"Unique exact-match brand keys: "
        f"{len(lookup):,}"
    )

    responses = load_responses(
        "beauty_products_groq.jsonl"
    )

    brand_responses = [
    response
    for response in responses
    if response["query_id"].startswith("brand_01_")
    ]

    brands = []

    for brand_response in brand_responses:
        extracted = extract_brands_from_response(
            brand_response["query_id"],
            brand_response["response_text"],
        )
        brands.extend(extracted)

    print()
    print(f"Brand responses processed: {len(brand_responses)}")
    print(f"Extracted brand mentions: {len(brands)}")

    matched = 0
    unmatched = 0

    print()
    print("Brand matching results:")
    print("=" * 80)

    for brand in brands:
        matched_store = match_brand(
            brand["brand_name"],
            lookup,
        )

        if matched_store:
            matched += 1
            status = "MATCHED"
        else:
            unmatched += 1
            status = "UNMATCHED"

        print(
            f"{brand['position']:>2}. "
            f"{brand['brand_name']:<25} "
            f"-> {matched_store} "
            f"[{status}]"
        )

    print()
    print("=" * 80)
    print(f"Matched:   {matched}")
    print(f"Unmatched: {unmatched}")

    if brands:
        print(f"Coverage:  {matched / len(brands) * 100:.2f}%")