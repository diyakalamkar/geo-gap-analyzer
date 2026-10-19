
import sys
from datetime import datetime

from app.geo_gap.query_templates import build_queries
from app.probing.tasks import probe_prompt
from app.probing.openrouter_provider import DEFAULT_MODEL
from app.probing.task_manifest import save_task_manifest


OUTPUT_FILE = "all_beauty_openrouter.jsonl"
CATEGORY = "All_Beauty"


def queue_openrouter_batch(start: int, end: int):
    """Queue a selected prompt range and save task-submission metadata."""

    queries = build_queries(CATEGORY)

    if not 0 <= start < end <= len(queries):
        raise ValueError(
            f"Invalid range {start}:{end}. "
            f"Available prompts: {len(queries)}"
        )

    batch = queries[start:end]
    task_records = []

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"openrouter_{CATEGORY}_{timestamp}"
    manifest_filename = f"openrouter_task_manifest_{timestamp}.json"

    print(f"Total prompts available: {len(queries)}")
    print(f"Queueing prompts {start + 1} to {end}")
    print(f"Provider: OpenRouter | Model: {DEFAULT_MODEL}")
    print(f"Output: {OUTPUT_FILE}")

    for index, query in enumerate(batch, start=start + 1):
        result = probe_prompt.delay(
            query,
            provider="openrouter",
            model=DEFAULT_MODEL,
            output_filename=OUTPUT_FILE,
            run_id=run_id,
        )

        task_record = {
            "task_id": result.id,
            "prompt_id": query.get("prompt_id"),
            "query_id": query.get("query_id"),
            "category": query.get("category", CATEGORY),
            "provider": "openrouter",
            "model": DEFAULT_MODEL,
            "output_file": OUTPUT_FILE,
            "run_id": run_id,
        }

        task_records.append(task_record)

        # Persist progress after each task is successfully queued.
        save_task_manifest(task_records, manifest_filename)

        print(
            f"[{index}/{len(queries)}] "
            f"{query.get('query_id')} -> {result.id}"
        )

    print(f"\nQueued {len(task_records)} OpenRouter tasks.")
    print(f"Manifest: {manifest_filename}")

    return [record["task_id"] for record in task_records]


if __name__ == "__main__":
    start = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    end = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    queue_openrouter_batch(start, end)