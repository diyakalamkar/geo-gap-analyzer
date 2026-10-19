import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from app.probing import task_status


class FakeAsyncResult:
    def __init__(self, state):
        self.state = state


class TaskStatusTests(unittest.TestCase):
    def test_reports_success_and_failure(self):
        manifest = {
            "task_count": 2,
            "tasks": [
                {
                    "task_id": "task-success",
                    "query_id": "query_success",
                    "provider": "groq",
                },
                {
                    "task_id": "task-failure",
                    "query_id": "query_failure",
                    "provider": "openrouter",
                },
            ],
        }

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test_manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")

            with (
                patch.object(
                    task_status,
                    "MANIFEST_DIR",
                    Path(directory),
                ),
                patch.object(
                    task_status.celery_app,
                    "AsyncResult",
                    side_effect=[
                        FakeAsyncResult("SUCCESS"),
                        FakeAsyncResult("FAILURE"),
                    ],
                ),
                patch("builtins.print") as mock_print,
            ):
                task_status.report_task_status("test_manifest.json")

        output = "\n".join(
            str(call.args[0])
            for call in mock_print.call_args_list
            if call.args
        )

        self.assertIn("SUCCESS: 1", output)
        self.assertIn("FAILURE: 1", output)
        self.assertIn("Completed successfully: 1/2", output)
        self.assertIn("Failed: 1/2", output)

    def test_missing_task_id_is_reported(self):
        manifest = {
            "tasks": [
                {
                    "query_id": "missing_id",
                    "provider": "groq",
                }
            ]
        }

        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test_manifest.json"
            path.write_text(json.dumps(manifest), encoding="utf-8")

            with (
                patch.object(
                    task_status,
                    "MANIFEST_DIR",
                    Path(directory),
                ),
                patch("builtins.print") as mock_print,
            ):
                task_status.report_task_status("test_manifest.json")

        output = "\n".join(
            str(call.args[0])
            for call in mock_print.call_args_list
            if call.args
        )
        self.assertIn("MISSING_TASK_ID: 1", output)


if __name__ == "__main__":
    unittest.main()