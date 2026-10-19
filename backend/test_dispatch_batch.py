import json
from unittest.mock import patch

from app.probing import tasks


def test_dispatch_batch_queues_capped_fanout():
    fake_queries = [
        {
            "prompt": f"Prompt {i}",
            "prompt_id": f"p{i}",
            "query_id": f"q{i}",
            "category": "All_Beauty",
        }
        for i in range(10)
    ]

    queued = []

    class FakeResult:
        def __init__(self, task_id):
            self.id = task_id

    def fake_apply_async(*, args, kwargs):
        task_id = f"task-{len(queued) + 1}"
        queued.append({"args": args, "kwargs": kwargs})
        return FakeResult(task_id)

    with (
        patch.object(tasks, "build_queries", return_value=fake_queries),
        patch.object(tasks.probe_prompt, "apply_async", side_effect=fake_apply_async),
        patch.object(tasks, "save_task_manifest") as save_manifest,
        patch.dict(
            "os.environ",
            {
                "GEO_GAP_CATEGORY": "All_Beauty",
                "GEO_GAP_PROMPT_CAP": "3",
                "GEO_GAP_PROVIDERS": "groq,openrouter",
            },
        ),
    ):
        result = tasks.dispatch_batch.run()

    assert result["prompt_count"] == 3
    assert result["provider_count"] == 2
    assert result["task_count"] == 6
    assert len(queued) == 6

    run_ids = {item["kwargs"]["run_id"] for item in queued}
    assert run_ids == {result["run_id"]}

    providers = [item["kwargs"]["provider"] for item in queued]
    assert providers.count("groq") == 3
    assert providers.count("openrouter") == 3

    assert save_manifest.call_count == 6
    manifest_tasks = save_manifest.call_args.args[0]
    assert len(manifest_tasks) == 6
    assert all(task["run_id"] == result["run_id"] for task in manifest_tasks)


if __name__ == "__main__":
    test_dispatch_batch_queues_capped_fanout()
    print("PASS: capped fan-out, shared run_id, and incremental manifest")
