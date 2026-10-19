import os

from groq import (
    Groq,
    APIConnectionError,
    APITimeoutError,
    APIStatusError,
)

from app.probing.provider_errors import (
    ProviderPermanentError,
    ProviderRetryableError,
)
from app.probing.request_throttle import wait_for_provider_slot


DEFAULT_MODEL = "qwen/qwen3.8-27b"


def get_client() -> Groq:
    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        raise ProviderPermanentError(
            "GROQ_API_KEY environment variable is not configured."
        )

    return Groq(api_key=api_key)


def generate_response(prompt: str, model: str = DEFAULT_MODEL) -> str:
    client = get_client()

    try:
        wait_for_provider_slot("groq")
        response = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_completion_tokens=4096,
        )
    except (APIConnectionError, APITimeoutError) as exc:
        raise ProviderRetryableError(
            f"Groq connection failure: {type(exc).__name__}"
        ) from exc
    except APIStatusError as exc:
        status_code = exc.status_code

        if status_code == 429 or status_code in (408, 425) or status_code >= 500:
            retry_after = None
            headers = getattr(getattr(exc, "response", None), "headers", {})

            if headers:
                try:
                    value = headers.get("Retry-After")
                    if value is not None:
                        retry_after = max(0.0, float(value))
                except (TypeError, ValueError):
                    retry_after = None

            raise ProviderRetryableError(
                f"Groq temporary HTTP failure: {status_code}",
                retry_after=retry_after,
            ) from exc

        raise ProviderPermanentError(
            f"Groq HTTP failure: {status_code}. "
            "Check the model, request, and API credentials."
        ) from exc

    choice = response.choices[0]

    return choice.message.content or ""


if __name__ == "__main__":
    test_prompt = (
        "Name three types of beauty and personal care products. "
        "Return only a short list."
    )

    print("Testing Groq connection...")
    print(f"Model: {DEFAULT_MODEL}")
    print()

    answer = generate_response(test_prompt)

    print("Response:")
    print(answer)
