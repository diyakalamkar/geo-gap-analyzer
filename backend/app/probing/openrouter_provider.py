import os
import requests
from app.probing.request_throttle import wait_for_provider_slot

from app.probing.provider_errors import (
    ProviderPermanentError,
    ProviderRetryableError,
)


DEFAULT_MODEL = "openrouter/free"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


def generate_response(
    prompt: str,
    model: str = DEFAULT_MODEL,
) -> str:
    api_key = os.getenv("OPENROUTER_API_KEY")

    if not api_key:
        raise ProviderPermanentError(
            "OPENROUTER_API_KEY environment variable is not configured."
        )

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0,
        "max_tokens": 4096,
    }

    try:
        wait_for_provider_slot("openrouter")
        response = requests.post(
            OPENROUTER_URL,
            headers=headers,
            json=payload,
            timeout=120,
        )
    except (requests.Timeout, requests.ConnectionError) as exc:
        raise ProviderRetryableError(
            f"OpenRouter connection failure: {type(exc).__name__}"
        ) from exc

    if response.status_code == 429 or response.status_code >= 500:
        retry_after = None
        header = response.headers.get("Retry-After")

        if header:
            try:
                retry_after = max(0.0, float(header))
            except (TypeError, ValueError):
                # Non-numeric Retry-After values fall back to backoff.
                retry_after = None

        raise ProviderRetryableError(
            f"OpenRouter temporary HTTP failure: {response.status_code}",
            retry_after=retry_after,
        )

    if response.status_code in (408, 425):
        raise ProviderRetryableError(
            f"OpenRouter temporary HTTP failure: {response.status_code}"
        )

    if response.status_code >= 400:
        raise ProviderPermanentError(
            f"OpenRouter HTTP failure: {response.status_code}. "
            "Check the model, request, and API credentials."
        )

    try:
        data = response.json()
        content = data["choices"][0]["message"]["content"]
    except (ValueError, KeyError, IndexError, TypeError) as exc:
        raise ProviderPermanentError(
            "OpenRouter returned an unexpected response structure."
        ) from exc

    return content or ""