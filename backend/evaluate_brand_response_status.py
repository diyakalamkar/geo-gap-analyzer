
import json
from pathlib import Path
from collections import Counter

from app.geo_gap.brand_extractor import (
    classify_brand_response,
    extract_brands_from_response,
)

ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "Groq": ROOT / "data/processed/geo_gap_responses/celery_probe_responses.jsonl",
    "OpenRouter": ROOT / "data/processed/geo_gap_responses/all_beauty_openrouter.jsonl",
}

for provider_name, path in FILES.items():
    print(f"\n{'=' * 55}")
    print(provider_name)

    with path.open("r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    records = [
        r for r in records
        if r.get("prompt_id") != "provider-smoke-test"
        and str(r.get("query_id", "")).startswith("brand_01_")
    ]

    statuses = Counter()
    total_extracted = 0

    for record in records:
        query_id = record.get("query_id", "")
        response_text = record.get("response_text", "")

        status = classify_brand_response(response_text)
        brands = extract_brands_from_response(
            query_id,
            response_text,
        )

        statuses[status] += 1
        total_extracted += len(brands)

        print(
            f"{query_id}: status={status}, "
            f"brands_extracted={len(brands)}"
        )

    print("\nTotal brand-list prompts:", len(records))
    print("Status counts:", dict(statuses))
    print("Total extracted brand mentions:", total_extracted)
