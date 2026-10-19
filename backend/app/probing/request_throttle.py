import os
import threading
import time


_lock = threading.Lock()
_last_request_started = {}


def wait_for_provider_slot(provider: str) -> None:
    """Apply a configurable minimum interval between requests per provider.

    This throttle is process-local; it does not coordinate separate workers.
    Set the interval to 0 to disable throttling.
    """
    env_name = f"{provider.upper()}_MIN_REQUEST_INTERVAL_SECONDS"

    try:
        interval = float(os.getenv(env_name, "1.0"))
    except ValueError as exc:
        raise ValueError(
            f"{env_name} must be a non-negative number."
        ) from exc

    if interval < 0:
        raise ValueError(f"{env_name} must be non-negative.")

    if interval == 0:
        return

    with _lock:
        now = time.monotonic()
        previous = _last_request_started.get(provider)

        if previous is not None:
            wait_seconds = interval - (now - previous)
            if wait_seconds > 0:
                time.sleep(wait_seconds)

        _last_request_started[provider] = time.monotonic()