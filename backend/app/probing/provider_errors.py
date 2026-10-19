
class ProviderRetryableError(Exception):
    """A provider failure that may succeed on retry."""

    def __init__(self, message: str, retry_after: float | None = None):
        super().__init__(message)
        self.retry_after = retry_after


class ProviderPermanentError(Exception):
    """A provider failure that should not be retried automatically."""