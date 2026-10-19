
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

GROQ_FILE = ROOT / "data/processed/geo_gap_responses/celery_probe_responses.jsonl"
OPENROUTER_FILE = ROOT / "data/processed/geo_gap_responses/all_beauty_openrouter.jsonl"


def load_records(path):
    with path.open("r", encoding="utf-8") as f:
        records = [json.loads(line) for line in f if line.strip()]

    return {
        r["prompt_id"]: r
        for r in records
        if r.get("prompt_id") != "provider-smoke-test"
    }


groq = load_records(GROQ_FILE)
openrouter = load_records(OPENROUTER_FILE)

groq_ids = set(groq)
openrouter_ids = set(openrouter)
common_ids = groq_ids & openrouter_ids

missing_from_groq = sorted(openrouter_ids - groq_ids)
missing_from_openrouter = sorted(groq_ids - openrouter_ids)

prompt_mismatches = [
    prompt_id
    for prompt_id in common_ids
    if groq[prompt_id].get("prompt") != openrouter[prompt_id].get("prompt")
]

query_mismatches = [
    prompt_id
    for prompt_id in common_ids
    if groq[prompt_id].get("query_id") != openrouter[prompt_id].get("query_id")
]

print("Groq prompt count:", len(groq))
print("OpenRouter prompt count:", len(openrouter))
print("Common prompt IDs:", len(common_ids))
print("Missing from Groq:", missing_from_groq)
print("Missing from OpenRouter:", missing_from_openrouter)
print("Prompt text mismatches:", len(prompt_mismatches))
print("Query ID mismatches:", len(query_mismatches))

if prompt_mismatches:
    print("\nExamples of prompt text mismatches:")
    for prompt_id in prompt_mismatches[:5]:
        print("\nPrompt ID:", prompt_id)
        print("Groq:", groq[prompt_id].get("prompt"))
        print("OpenRouter:", openrouter[prompt_id].get("prompt"))

if query_mismatches:
    print("\nQuery ID mismatches:", query_mismatches[:10])

if (
    len(common_ids) == 40
    and not missing_from_groq
    and not missing_from_openrouter
    and not prompt_mismatches
    and not query_mismatches
):
    print("\nPASS: Both providers received the same 40 prompts.")
else:
    print("\nCHECK REQUIRED: Investigate the mismatches above.")