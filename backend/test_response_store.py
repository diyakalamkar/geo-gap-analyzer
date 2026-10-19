import json
import uuid

from app.geo_gap.response_schema import LLMResponse
from app.geo_gap.response_store import OUTPUT_DIR, append_response


def make_response(prompt_id):
    return LLMResponse(
        provider="groq",
        model="test-model",
        category="test",
        query_id="idempotency_test",
        intent="test",
        prompt="Local test prompt",
        response_text="Local test response",
        product_mentions=[],
        prompt_id=prompt_id,
    )


def main():
    filename = f"_idempotency_test_{uuid.uuid4().hex}.jsonl"
    path = OUTPUT_DIR / filename
    prompt_id = f"local-test-{uuid.uuid4().hex}"

    try:
        first_path = append_response(
            make_response(prompt_id),
            filename,
            deduplicate=True,
        )

        second_path = append_response(
            make_response(prompt_id),
            filename,
            deduplicate=True,
        )

        with second_path.open("r", encoding="utf-8") as file:
            records = [
                json.loads(line)
                for line in file
                if line.strip()
            ]

        assert first_path == second_path
        assert len(records) == 1
        assert records[0]["prompt_id"] == prompt_id

        print("PASS: duplicate response was not appended.")
        print(f"Records saved: {len(records)}")

    finally:
        if path.exists():
            path.unlink()


if __name__ == "__main__":
    main()