from unittest.mock import Mock, patch

import requests

from app.probing.provider_errors import (
    ProviderPermanentError,
    ProviderRetryableError,
)
from app.probing.openrouter_provider import (
    generate_response as generate_openrouter_response,
)
from app.geo_gap.groq_provider import (
    generate_response as generate_groq_response,
)


def fake_http_response(status_code, headers=None):
    """Build a mocked requests.Response."""
    response = Mock(spec=requests.Response)
    response.status_code = status_code
    response.headers = headers or {}
    return response


def check_openrouter_status(status_code, expected_exception):
    response = fake_http_response(status_code)

    with patch.dict("os.environ", {"OPENROUTER_API_KEY": "test-key"}):
        with patch(
            "app.probing.openrouter_provider.requests.post",
            return_value=response,
        ):
            try:
                generate_openrouter_response(
                    "test prompt",
                    model="openrouter/free",
                )
            except expected_exception:
                return
            except Exception as exc:
                raise AssertionError(
                    f"OpenRouter HTTP {status_code}: expected "
                    f"{expected_exception.__name__}, got "
                    f"{type(exc).__name__}: {exc}"
                ) from exc

    raise AssertionError(
        f"OpenRouter HTTP {status_code}: expected "
        f"{expected_exception.__name__}, but no exception was raised"
    )


def check_groq_status(status_code, expected_exception):
    # Groq SDK status exceptions use an HTTP response and request.
    http_response = Mock()
    http_response.status_code = status_code
    http_response.headers = {}

    request = Mock()
    error = __import__("groq").APIStatusError(
        f"Simulated Groq HTTP {status_code}",
        response=http_response,
        body=None,
    )

    with patch(
        "app.geo_gap.groq_provider.get_client"
    ) as mock_get_client:
        client = mock_get_client.return_value
        client.chat.completions.create.side_effect = error

        try:
            generate_groq_response(
                "test prompt",
                model="qwen/qwen3.8-27b",
            )
        except expected_exception:
            return
        except Exception as exc:
            raise AssertionError(
                f"Groq HTTP {status_code}: expected "
                f"{expected_exception.__name__}, got "
                f"{type(exc).__name__}: {exc}"
            ) from exc

    raise AssertionError(
        f"Groq HTTP {status_code}: expected "
        f"{expected_exception.__name__}, but no exception was raised"
    )


def main():
    cases = [
        (429, ProviderRetryableError),
        (503, ProviderRetryableError),
        (401, ProviderPermanentError),
    ]

    for status_code, expected in cases:
        check_openrouter_status(status_code, expected)
        print(f"OpenRouter HTTP {status_code}: PASS")

    for status_code, expected in cases:
        check_groq_status(status_code, expected)
        print(f"Groq HTTP {status_code}: PASS")

    print("\nAll provider error-handling tests passed.")


if __name__ == "__main__":
    main()