
import json
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[1]

FILES = {
    "Groq": ROOT / "data/processed/geo_gap_responses/celery_probe_responses.jsonl",
    "OpenRouter": ROOT / "data/processed/geo_gap_responses/all_beauty_openrouter.jsonl",
}

for provider_name, path in FILES.items():
    print(f"\n{'=' * 60}")
    print(f"PROVIDER: {provider_name}")
    print(f"FILE: {path}")

    if not path.exists():
        print("ERROR: File not found.")
        continue

    records = []
    malformed = 0

    with path.open("r", encoding="utf-8") as f:
        for line_number, line in enumerate(f, start=1):
            if not line.strip():
                continue
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                malformed += 1
                print(f"Malformed JSON on line {line_number}")

    print("Total valid records:", len(records))
    print("Malformed JSON lines:", malformed)

    if not records:
        continue

    print("Available fields:", sorted({
        key for record in records for key in record
    }))

    providers = Counter(
        str(r.get("provider", "<missing>")) for r in records
    )
    models = Counter(
        str(r.get("model", "<missing>")) for r in records
    )

    smoke_tests = [
        r for r in records
        if r.get("prompt_id") == "provider-smoke-test"
    ]
    actual = [
        r for r in records
        if r.get("prompt_id") != "provider-smoke-test"
    ]

    prompt_ids = [
        r.get("prompt_id") for r in actual
        if r.get("prompt_id") is not None
    ]

    empty_responses = [
        r for r in actual
        if not str(
            r.get("response_text", r.get("response", "")) or ""
        ).strip()
    ]

    print("Provider counts:", dict(providers))
    print("Model counts:", dict(models))
    print("Smoke-test records:", len(smoke_tests))
    print("Records excluding smoke tests:", len(actual))
    print("Unique prompt IDs:", len(set(prompt_ids)))
    print("Duplicate prompt IDs:", len(prompt_ids) - len(set(prompt_ids)))
    print("Records missing prompt_id:", sum(
        r.get("prompt_id") is None for r in actual
    ))
    print("Empty responses:", len(empty_responses))

    print("\nSample record keys and values:")
    sample = actual[0] if actual else records[0]
    for key, value in sample.items():
        print(f"  {key}: {str(value)[:180]}")