import os
import unittest
from unittest.mock import patch

from app.probing.request_throttle import wait_for_provider_slot


class RequestThrottleTests(unittest.TestCase):
    def test_zero_interval_does_not_sleep(self):
        with (
            patch.dict(
                os.environ,
                {"GROQ_MIN_REQUEST_INTERVAL_SECONDS": "0"},
            ),
            patch("app.probing.request_throttle.time.sleep") as sleep,
        ):
            wait_for_provider_slot("groq")
            wait_for_provider_slot("groq")

        sleep.assert_not_called()

    def test_negative_interval_is_rejected(self):
        with patch.dict(
            os.environ,
            {"GROQ_MIN_REQUEST_INTERVAL_SECONDS": "-1"},
        ):
            with self.assertRaises(ValueError):
                wait_for_provider_slot("groq")

    def test_invalid_interval_is_rejected(self):
        with patch.dict(
            os.environ,
            {"GROQ_MIN_REQUEST_INTERVAL_SECONDS": "invalid"},
        ):
            with self.assertRaises(ValueError):
                wait_for_provider_slot("groq")


if __name__ == "__main__":
    unittest.main()