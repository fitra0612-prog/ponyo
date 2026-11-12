"""Regression tests for the Saweria simulation CLI exit status."""
from unittest.mock import patch

from test import test_saweria


def test_send_test_donation_returns_false_when_receiver_is_unreachable():
    def fail(*args, **kwargs):
        raise OSError("receiver offline")

    with patch.object(test_saweria.urllib.request, "urlopen", fail):
        assert test_saweria.send_test_donation(
            "Audit", 1000, "test", port=49227, stream_key=""
        ) is False


def test_send_test_donation_returns_true_on_success():
    class Response:
        status = 200

        def read(self):
            return b'{"status":"ok"}'

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    with patch.object(test_saweria.urllib.request, "urlopen", lambda *args, **kwargs: Response()):
        assert test_saweria.send_test_donation(
            "Audit", 1000, "test", port=49227, stream_key=""
        ) is True


if __name__ == "__main__":
    print("Run with pytest or a compatible monkeypatch fixture")
