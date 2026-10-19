import time

from app.geo_gap.query_templates import build_queries
from app.geo_gap.groq_provider import generate_response, DEFAULT_MODEL
from app.geo_gap.response_schema import LLMResponse
from app.geo_gap.response_store import save_responses
from app.probing.provider_errors import (
    ProviderPermanentError,
    ProviderRetryableError,
)

MAX_RETRIES = 3
RETRY_DELAY_SECONDS = 2

def generate_with_retry(prompt: str) -> str:
    """Generate an LLM response with basic retry handling."""

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            return generate_response(
                prompt,
                model=DEFAULT_MODEL,
            )

        except ProviderPermanentError as error:
            print(f"  Permanent failure: {error}")
            return ""

        except ProviderRetryableError as error:
            print(
                f"  Temporary provider failure "
                f"(attempt {attempt}/{MAX_RETRIES}): {error}"
            )

            if attempt < MAX_RETRIES:
                delay = (
                    error.retry_after
                    if error.retry_after is not None
                    else RETRY_DELAY_SECONDS
                )
                time.sleep(max(0, delay))

        except Exception as error:
            print(
                f"  Request failed "
                f"(attempt {attempt}/{MAX_RETRIES}): {error}"
            )

            if attempt < MAX_RETRIES:
                time.sleep(RETRY_DELAY_SECONDS)

    print("  Failed after all retries.")
    return ""

def run_category(category: str):
    queries = build_queries(category)

    responses = []

    print(f"Generated {len(queries)} queries.")
    print()

    for index, query in enumerate(queries, start=1):

        print("=" * 80)
        print(f"[{index}/{len(queries)}] Query ID: {query['query_id']}")
        print(f"Base Query: {query['base_query_id']}")
        print(f"Intent: {query['intent']}")
        print(f"Persona: {query['persona']}")
        print(f"Prompt: {query['prompt']}")
        print()

        response_text = generate_with_retry(query["prompt"])

        if response_text:
            print("LLM Response:")
            print(response_text)
        else:
            print("LLM Response: FAILED")

        print()

        response = LLMResponse(
            provider="groq",
            model=DEFAULT_MODEL,
            category=category,
            query_id=query["query_id"],
            intent=query["intent"],
            prompt=query["prompt"],
            response_text=response_text,
            product_mentions=[],
        )

        responses.append(response)

    return responses

if __name__ == "__main__":
    category = "All_Beauty"

    print("=" * 80)
    print("GEO-GAP LLM PROBING")
    print("=" * 80)
    print(f"Category: {category}")
    print(f"Model: {DEFAULT_MODEL}")
    print()

    results = run_category(category)

    output_path = save_responses(
        results,
        "beauty_products_groq.jsonl",
    )

    successful = sum(
        1 for response in results
        if response.response_text
    )

    failed = len(results) - successful

    print("=" * 80)
    print("RUN COMPLETED")
    print("=" * 80)
    print(f"Total queries: {len(results)}")
    print(f"Successful: {successful}")
    print(f"Failed: {failed}")
    print(f"Saved responses to: {output_path}")
