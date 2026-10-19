
import json
from pathlib import Path
from datetime import datetime, timezone


# Resolve the project root from:
# backend/app/probing/task_manifest.py
PROJECT_ROOT = Path(__file__).resolve().parents[3]

MANIFEST_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "geo_gap_responses"
)


def save_task_manifest(tasks: list[dict], filename: str) -> Path:
    """Save task-submission metadata as a JSON manifest."""

    MANIFEST_DIR.mkdir(parents=True, exist_ok=True)
    path = MANIFEST_DIR / filename

    manifest = {
        "created_at_utc": datetime.now(timezone.utc).isoformat(),
        "task_count": len(tasks),
        "tasks": tasks,
    }

    with path.open("w", encoding="utf-8") as file:
        json.dump(manifest, file, indent=2, ensure_ascii=False)

    print(f"Task manifest saved: {path}")
    return path