from pathlib import Path

import pandas as pd

from app.geo_gap.name_normalizer import normalize_name


PROJECT_ROOT = Path(__file__).resolve().parents[3]

GROUND_TRUTH_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "exports"
    / "geo_gap_product_ground_truth.parquet"
)


def load_ground_truth() -> pd.DataFrame:
    """Load the Geo-Gap product ground truth."""
    return pd.read_parquet(
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


def build_product_lookup(df: pd.DataFrame) -> dict:
    """
    Build an exact normalized-name lookup.

    Only unique normalized product names are stored.
    Ambiguous normalized names are excluded so that
    a product is never assigned to an arbitrary ASIN.
    """
    normalized = df["product_title"].map(normalize_name)

    grouped = (
        pd.DataFrame(
            {
                "normalized_name": normalized,
                "parent_asin": df["parent_asin"],
            }
        )
        .groupby("normalized_name")["parent_asin"]
        .agg(list)
    )

    lookup = {}

    for normalized_name, parent_asins in grouped.items():
        if normalized_name and len(parent_asins) == 1:
            lookup[normalized_name] = parent_asins[0]

    return lookup


def match_product(product_name: str, lookup: dict):
    """Return the matched parent_asin or None."""
    normalized_name = normalize_name(product_name)

    if not normalized_name:
        return None

    return lookup.get(normalized_name)


if __name__ == "__main__":
    print("Loading Geo-Gap ground truth...")
    ground_truth = load_ground_truth()

    print(f"Ground-truth rows: {len(ground_truth):,}")

    lookup = build_product_lookup(ground_truth)

    print(f"Unique exact-match keys: {len(lookup):,}")

    test_names = [
        ground_truth.iloc[0]["product_title"],
        ground_truth.iloc[1]["product_title"],
        "This product does not exist in the ground truth",
    ]

    print()
    print("Exact-match tests:")

    for name in test_names:
        matched_asin = match_product(name, lookup)

        print()
        print(f"Input: {name}")
        print(f"Matched ASIN: {matched_asin}")