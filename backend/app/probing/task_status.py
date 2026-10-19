import argparse
import json
from collections import Counter
from pathlib import Path

from app.probing.celery_app import celery_app
from app.probing.task_manifest import MANIFEST_DIR


def load_manifest(filename: str) -> dict:
    """Load a task manifest from the response-data directory."""

    path = Path(filename)

    # Accept either a manifest filename or an explicit path.
    if not path.is_absolute():
        path = MANIFEST_DIR / path

    if not path.is_file():
        raise FileNotFoundError(f"Manifest not found: {path}")

    with path.open("r", encoding="utf-8") as file:
        manifest = json.load(file)

    if not isinstance(manifest.get("tasks"), list):
        raise ValueError("Invalid manifest: 'tasks' must be a list.")

    return manifest


def report_task_status(filename: str) -> None:
    """Report current Celery states without printing model responses."""

    manifest = load_manifest(filename)
    tasks = manifest["tasks"]

    print(f"Manifest: {filename}")
    print(f"Submitted tasks: {len(tasks)}")
    print("-" * 90)

    counts = Counter()

    for task in tasks:
        task_id = task.get("task_id")

        if not task_id:
            state = "MISSING_TASK_ID"
        else:
            state = celery_app.AsyncResult(task_id).state

        counts[state] += 1

        print(
            f"{task.get('query_id', 'unknown_query')} | "
            f"{task.get('provider', 'unknown_provider')} | "
            f"{state} | "
            f"{task_id or 'NO_TASK_ID'}"
        )

    print("-" * 90)
    print("Status summary:")

    for state, count in sorted(counts.items()):
        print(f"  {state}: {count}")

    completed = counts.get("SUCCESS", 0)
    failed = counts.get("FAILURE", 0)
    print(f"\nCompleted successfully: {completed}/{len(tasks)}")
    print(f"Failed: {failed}/{len(tasks)}")

    if counts.get("PENDING", 0):
        print(
            "Note: PENDING means the backend has no later recorded state; "
            "it does not prove that the task is waiting in the queue."
        )


def main():
    parser = argparse.ArgumentParser(
        description="Inspect Celery task states from a saved manifest."
    )
    parser.add_argument(
        "manifest",
        help="Manifest filename, e.g. groq_task_manifest_20261011_060000.json",
    )
    args = parser.parse_args()

    try:
        report_task_status(args.manifest)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()