import json
from pathlib import Path

from app.geo_gap.brand_extractor import extract_brands_from_response
from app.geo_gap.brand_matcher import (
    load_brand_ground_truth,
    build_brand_lookup,
    match_brand,
)

base = Path("..") / "data" / "processed" / "geo_gap_responses"
files = {
    "Groq": "celery_probe_responses.jsonl",
    "OpenRouter": "all_beauty_openrouter.jsonl",
}

ground_truth = load_brand_ground_truth()
lookup = build_brand_lookup(ground_truth)

print("Ground-truth brands loaded:", len(lookup))

for provider, filename in files.items():
    path = base / filename
    rows = [
        json.loads(line)
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]

    rows = [
        row for row in rows
        if row.get("prompt_id") != "provider-smoke-test"
        and str(row.get("query_id", "")).startswith("brand_01_")
    ]

    extracted_count = 0
    matched_count = 0

    print(f"\n{'=' * 55}\n{provider}")
    print("Brand-query responses:", len(rows))

    for row in rows:
        mentions = extract_brands_from_response(
            row.get("query_id", ""),
            row.get("response_text", "") or "",
        )

        print(f"\n{row.get('query_id')}: {len(mentions)} brands extracted")

        for mention in mentions:
            name = mention["brand_name"]
            matched = match_brand(name, lookup)

            extracted_count += 1
            if matched:
                matched_count += 1

            print(
                f"  Position {mention['position']}: {name}"
                f" -> {'MATCH: ' + str(matched) if matched else 'NO MATCH'}"
            )

    coverage = (
        100 * matched_count / extracted_count
        if extracted_count else 0
    )
    print(f"\nTotal extracted: {extracted_count}")
    print(f"Matched to ground truth: {matched_count}")
    print(f"Matching coverage: {coverage:.1f}%")
