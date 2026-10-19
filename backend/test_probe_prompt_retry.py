
from pathlib import Path
from app.probing.provider_errors import ProviderRetryableError
import app.probing.tasks as tasks


# Simulate a provider that fails twice and succeeds on its third call.
provider_calls = 0
saved_responses = []


def fake_groq_response(prompt, model):
    global provider_calls
    provider_calls += 1

    if provider_calls <= 2:
        raise ProviderRetryableError("Simulated temporary provider failure")

    return "Simulated successful response"


def fake_append_response(response, output_filename, *, deduplicate=False):
    # Record the response in memory; do not write any file.
    saved_responses.append(response)
    return Path("mocked-output.jsonl")


# Replace external dependencies only in this test process.
tasks.generate_groq_response = fake_groq_response
tasks.append_response = fake_append_response

prompt_record = {
    "prompt_id": "retry-test-001",
    "query_id": "retry_test",
    "category": "test",
    "intent": "test_retry",
    "prompt": "This is a simulated prompt.",
    "persona": "test",
    "target_brands": [],
}

result = tasks.probe_prompt.apply(
    args=[prompt_record],
    kwargs={
        "provider": "groq",
        "model": tasks.GROQ_DEFAULT_MODEL,
        "output_filename": "DO_NOT_WRITE_TEST.jsonl",
    },
    throw=False,
)

print("Task state:", result.state)
print("Provider calls:", provider_calls)
print("Responses saved (mocked):", len(saved_responses))
print("Task result:", result.result)

assert result.successful(), "Task did not succeed"
assert provider_calls == 3, f"Expected 3 calls, got {provider_calls}"
assert len(saved_responses) == 1, (
    f"Expected 1 mocked save, got {len(saved_responses)}"
)
assert result.result["response_text"] == "Simulated successful response"

print("\nPASS: probe_prompt retried twice and saved one response.")
