import json
from pathlib import Path
from typing import List

from .response_schema import LLMResponse


PROJECT_ROOT = Path(__file__).resolve().parents[3]

OUTPUT_DIR = (
    PROJECT_ROOT
    / "data"
    / "processed"
    / "geo_gap_responses"
)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def save_responses(
    responses: List[LLMResponse],
    filename: str,
) -> Path:
    """
    Save LLM responses as JSONL.

    Each line represents one LLM response.
    """

    if not filename.endswith(".jsonl"):
        raise ValueError("filename must end with .jsonl")

    output_path = OUTPUT_DIR / filename

    with output_path.open(
        "w",
        encoding="utf-8",
    ) as file:

        for response in responses:
            file.write(
                json.dumps(
                    response.to_dict(),
                    ensure_ascii=False,
                )
                + "\n"
            )

    return output_path

def append_response(
    response: LLMResponse,
    filename: str,
    *,
    deduplicate: bool = False,
) -> Path:
    """
    Append one LLM response to a JSONL file.

    If deduplicate=True and prompt_id is present, skip an append
    when the same prompt_id, provider, and model already exist.
    """

    if not filename.endswith(".jsonl"):
        raise ValueError("filename must end with .jsonl")

    output_path = OUTPUT_DIR / filename
    response_data = response.to_dict()

    if deduplicate and response_data.get("prompt_id"):
        if output_path.exists():
            with output_path.open("r", encoding="utf-8") as file:
                for line in file:
                    line = line.strip()
                    if not line:
                        continue

                    try:
                        existing = json.loads(line)
                    except json.JSONDecodeError:
                        # Don't treat malformed lines as matching records.
                        continue

                    if (
                        existing.get("prompt_id")
                        == response_data["prompt_id"]
                        and existing.get("provider")
                        == response_data["provider"]
                        and existing.get("model")
                        == response_data["model"]
                    ):
                        return output_path

    with output_path.open("a", encoding="utf-8") as file:
        file.write(
            json.dumps(
                response_data,
                ensure_ascii=False,
            )
            + "\n"
        )

    return output_path

def load_responses(filename: str) -> List[dict]:
    """
    Load previously saved LLM responses.
    """

    input_path = OUTPUT_DIR / filename

    if not input_path.exists():
        raise FileNotFoundError(
            f"Response file not found: {input_path}"
        )

    responses = []

    with input_path.open(
        "r",
        encoding="utf-8",
    ) as file:

        for line in file:
            line = line.strip()

            if line:
                responses.append(
                    json.loads(line)
                )

    return responses


if __name__ == "__main__":
    test_response = LLMResponse(
        provider="test",
        model="test-model",
        category="beauty products",
        query_id="test_01",
        intent="test",
        prompt="Test prompt",
        response_text="Test response",
        product_mentions=[],
    )

    path = save_responses(
        [test_response],
        "test_response.jsonl",
    )

    print(f"[OK] Saved: {path}")

    loaded = load_responses(
        "test_response.jsonl"
    )

    print(f"[OK] Loaded responses: {len(loaded)}")

    print()
    print("Loaded response:")
    print(loaded[0])
