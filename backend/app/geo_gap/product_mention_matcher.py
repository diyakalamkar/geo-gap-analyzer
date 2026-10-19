from pathlib import Path

import pandas as pd

from app.geo_gap.product_matcher import (
    load_ground_truth,
    build_product_lookup,
    match_product,
)
from app.geo_gap.response_extractor import extract_products_from_response
from app.geo_gap.response_store import load_responses


PROJECT_ROOT = Path(__file__).resolve().parents[3]

OUTPUT_PATH = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "geo_gap_product_mentions.parquet"
)


def main():
    print("Loading product ground truth...")

    ground_truth = load_ground_truth()

    print(f"Ground-truth rows: {len(ground_truth):,}")

    lookup = build_product_lookup(ground_truth)

    print(f"Unique exact-match product keys: {len(lookup):,}")

    print()
    print("Loading LLM responses...")

    responses = load_responses(
        "beauty_products_groq.jsonl"
    )

    print(f"LLM responses: {len(responses)}")

    rows = []

    for response in responses:
        query_id = response["query_id"]

        products = extract_products_from_response(
            query_id,
            response["response_text"],
        )

        for product in products:
            matched_asin = match_product(
                product["product_name"],
                lookup,
            )

            matched = matched_asin is not None

            rows.append(
                {
                    "query_id": query_id,
                    "position": product["position"],
                    "llm_product_name": product["product_name"],
                    "matched_parent_asin": matched_asin,
                    "matched": matched,
                }
            )

    mentions = pd.DataFrame(rows)

    print()
    print("=" * 80)
    print("PRODUCT MENTION MATCHING")
    print("=" * 80)

    print(f"Total product mentions: {len(mentions):,}")

    matched_count = int(
        mentions["matched"].sum()
    )

    unmatched_count = len(mentions) - matched_count

    coverage = (
        matched_count / len(mentions) * 100
        if len(mentions) > 0
        else 0
    )

    print(f"Matched:   {matched_count:,}")
    print(f"Unmatched: {unmatched_count:,}")
    print(f"Coverage:  {coverage:.2f}%")

    print()
    print("Mentions by query:")
    print(
        mentions.groupby("query_id")
        .size()
        .to_string()
    )

    print()
    print("Matches by query:")

    query_summary = (
        mentions
        .groupby("query_id")
        .agg(
            total_mentions=("llm_product_name", "size"),
            matched_mentions=("matched", "sum"),
        )
    )

    query_summary["coverage_pct"] = (
        query_summary["matched_mentions"]
        / query_summary["total_mentions"]
        * 100
    )

    print(query_summary.to_string())

    print()
    print("Unmatched product mentions:")

    unmatched = mentions[
        ~mentions["matched"]
    ]

    if unmatched.empty:
        print("None")
    else:
        for _, row in unmatched.iterrows():
            print(
                f"{row['query_id']} | "
                f"position={row['position']} | "
                f"{row['llm_product_name']}"
            )

    mentions.to_parquet(
        OUTPUT_PATH,
        index=False,
    )

    print()
    print("=" * 80)
    print(f"Saved to: {OUTPUT_PATH}")
    print("=" * 80)


if __name__ == "__main__":
    main()