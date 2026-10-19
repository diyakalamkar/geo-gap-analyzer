import json
from pathlib import Path

import pandas as pd

from app.geo_gap.brand_extractor import extract_brands_from_response
from app.geo_gap.brand_matcher import (
    GROUND_TRUTH_PATH,
    build_brand_lookup,
    load_brand_ground_truth,
    match_brand,
)
from app.geo_gap.name_normalizer import normalize_name

PROJECT_ROOT = Path(__file__).resolve().parents[1]
RESPONSE_DIR = PROJECT_ROOT / "data" / "processed" / "geo_gap_responses"
OUTPUT_DIR = PROJECT_ROOT / "data" / "processed" / "exports"

CATEGORY = "All_Beauty"

PROVIDERS = {
    "groq": "celery_probe_responses.jsonl",
    "openrouter": "all_beauty_openrouter.jsonl",
}


def read_responses(filename):
    path = RESPONSE_DIR / filename
    if not path.exists():
        raise FileNotFoundError(f"Response file not found: {path}")

    return [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Use only the requested category for matching and merit scores.
    ground_truth = load_brand_ground_truth()
    ground_truth = ground_truth[
        (ground_truth["category"] == CATEGORY)
        & ground_truth["store"].notna()
    ].copy()

    ground_truth["normalized_name"] = ground_truth["store"].map(
        normalize_name
    )
    ground_truth = ground_truth[
        ground_truth["normalized_name"] != ""
    ]

    lookup = build_brand_lookup(ground_truth)

    # One merit score per ground-truth store.
    brand_merit = (
        ground_truth.groupby("store", as_index=False)
        .agg(ground_truth_merit_score=("ground_truth_merit_score", "mean"))
    )

    print(f"Category: {CATEGORY}")
    print(f"Ground-truth rows: {len(ground_truth):,}")
    print(f"Unique normalized lookup names: {len(lookup):,}")
    print(f"Unique ground-truth stores: {len(brand_merit):,}")

    for provider, filename in PROVIDERS.items():
        rows = read_responses(filename)

        # Exclude smoke tests; keep all four intended brand-list prompts
        # in the denominator, including responses with no extractable table.
        rows = [
            row for row in rows
            if row.get("prompt_id") != "provider-smoke-test"
            and str(row.get("query_id", "")).startswith("brand_01_")
        ]

        # Protect against duplicate response rows for the same prompt.
        by_query = {}
        for row in rows:
            query_id = row.get("query_id", "")
            if query_id and query_id not in by_query:
                by_query[query_id] = row

        rows = list(by_query.values())
        total_prompts = len(rows)
        mentions = []

        for row in rows:
            query_id = row.get("query_id", "")
            response_text = row.get("response_text", "") or ""

            extracted = extract_brands_from_response(
                query_id, response_text
            )

            for item in extracted:
                matched_store = match_brand(item["brand_name"], lookup)

                mentions.append({
                    "provider": provider,
                    "category": CATEGORY,
                    "query_id": query_id,
                    "position": item["position"],
                    "llm_brand_name": item["brand_name"],
                    "matched_store": matched_store,
                    "matched": matched_store is not None,
                })

        mentions_df = pd.DataFrame(
            mentions,
            columns=[
                "provider", "category", "query_id", "position",
                "llm_brand_name", "matched_store", "matched",
            ],
        )

        # Save every extracted mention, including unmatched names.
        mentions_path = OUTPUT_DIR / f"llm_brand_mentions_{provider}_all_beauty.parquet"
        mentions_df.to_parquet(mentions_path, index=False)

        # Visibility is based on matched brands and all attempted
        # structured brand-list prompts, not just successful responses.
        matched_mentions = mentions_df[mentions_df["matched"]].copy()

        if not matched_mentions.empty:
            visibility = (
                matched_mentions.groupby("matched_store")
                .agg(
                    mention_count=("query_id", "size"),
                    prompts_mentioned=("query_id", "nunique"),
                    mean_position=("position", "mean"),
                )
                .reset_index()
                .rename(columns={"matched_store": "store"})
            )

            visibility["query_coverage"] = (
                visibility["prompts_mentioned"] / total_prompts
                if total_prompts else 0.0
            )
            visibility["visibility_score"] = (
                visibility["mention_count"]
                * visibility["query_coverage"]
                / visibility["mean_position"]
            )
        else:
            visibility = pd.DataFrame(columns=[
                "store", "mention_count", "prompts_mentioned",
                "mean_position", "query_coverage", "visibility_score",
            ])

        visibility_path = OUTPUT_DIR / f"brand_visibility_{provider}_all_beauty.parquet"
        visibility.to_parquet(visibility_path, index=False)

        # Keep the raw merit and visibility scales separate for now.
        gap = brand_merit.merge(visibility, on="store", how="left")
        for column in [
            "mention_count", "prompts_mentioned",
            "mean_position", "query_coverage", "visibility_score",
        ]:
            gap[column] = gap[column].fillna(0)

        gap_path = OUTPUT_DIR / f"brand_comparison_{provider}_all_beauty.parquet"
        gap.to_parquet(gap_path, index=False)

        extracted_count = len(mentions_df)
        matched_count = int(mentions_df["matched"].sum()) if extracted_count else 0
        prompts_with_mentions = (
            mentions_df.loc[mentions_df["matched"], "query_id"].nunique()
            if extracted_count else 0
        )

        print(f"\n--- {provider.upper()} ---")
        print(f"Brand-list prompts processed: {total_prompts}")
        print(f"Prompts with matched mentions: {prompts_with_mentions}")
        print(f"Brands extracted: {extracted_count}")
        print(f"Matched mentions: {matched_count}")
        print(
            "Matching coverage: "
            f"{matched_count / extracted_count * 100:.1f}%"
            if extracted_count else "Matching coverage: N/A (no brands extracted)"
        )
        print(f"Mentions file: {mentions_path.name}")
        print(f"Visibility file: {visibility_path.name}")
        print(f"Comparison file: {gap_path.name}")

    print("\nDone. Existing pipeline output files were not overwritten.")


if __name__ == "__main__":
    main()
