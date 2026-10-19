from datetime import datetime

from app.geo_gap.query_templates import build_queries
from app.geo_gap.groq_provider import DEFAULT_MODEL
from app.probing.tasks import probe_prompt
from app.probing.task_manifest import save_task_manifest


OUTPUT_FILE = "celery_probe_responses.jsonl"
CATEGORY = "All_Beauty"


def queue_category(category: str):
    """Build prompts, queue them through Celery, and track task IDs."""

    queries = build_queries(category)

    print(f"Generated {len(queries)} prompts for {category}.")
    print("Queuing prompts through Celery...")

    task_records = []

    # Keep one unique manifest filename for this batch.
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_id = f"groq_{category}_{timestamp}"
    manifest_filename = f"groq_task_manifest_{timestamp}.json"

    for index, query in enumerate(queries, start=1):
        result = probe_prompt.delay(
            query,
            provider="groq",
            model=DEFAULT_MODEL,
            output_filename=OUTPUT_FILE,
            run_id=run_id,
        )

        task_record = {
            "task_id": result.id,
            "prompt_id": query.get("prompt_id"),
            "query_id": query.get("query_id"),
            "category": query.get("category", category),
            "provider": "groq",
            "model": DEFAULT_MODEL,
            "output_file": OUTPUT_FILE,
            "run_id": run_id,
        }

        task_records.append(task_record)

        # Save after each successful submission so earlier task IDs
        # remain recorded if a later submission fails.
        save_task_manifest(task_records, manifest_filename)

        print(
            f"[{index}/{len(queries)}] "
            f"{query.get('query_id')} -> {result.id}"
        )

    print(f"\nQueued {len(task_records)} Groq Celery tasks.")
    print(f"Manifest: {manifest_filename}")

    return [record["task_id"] for record in task_records]


if __name__ == "__main__":
    queue_category(CATEGORY)