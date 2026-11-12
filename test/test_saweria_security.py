"""Security regression tests for mandatory Saweria webhook signatures."""
import hashlib
import hmac
import json
import time
import urllib.error
import urllib.request

from saweria_receiver import SaweriaReceiver


PORT = 49226
STREAM_KEY = "audit-stream-key"


def _payload():
    return {
        "version": "2022.01",
        "id": "security-test",
        "amount_raw": 1000,
        "donator_name": "Audit Donor",
        "donator_email": "audit@example.com",
        "message": "security test",
    }


def _signature(payload, key=STREAM_KEY):
    message = (
        f"{payload['version']}{payload['id']}{payload['amount_raw']}"
        f"{payload['donator_name']}{payload['donator_email']}"
    )
    return hmac.new(key.encode(), message.encode(), hashlib.sha256).hexdigest()


def _post(headers):
    body = json.dumps(_payload()).encode("utf-8")
    request = urllib.request.Request(
        f"http://127.0.0.1:{PORT}/webhook",
        data=body,
        headers={"Content-Type": "application/json", **headers},
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=2) as response:
            return response.status
    except urllib.error.HTTPError as exc:
        return exc.code


def test_missing_signature_is_rejected_when_stream_key_configured():
    receiver = SaweriaReceiver(port=PORT, stream_key=STREAM_KEY, host="127.0.0.1")
    receiver.start()
    time.sleep(0.05)
    try:
        assert _post({}) == 401
        assert receiver.get_next_donation() is None
    finally:
        receiver.stop()


def test_invalid_signature_is_rejected_when_stream_key_configured():
    receiver = SaweriaReceiver(port=PORT, stream_key=STREAM_KEY, host="127.0.0.1")
    receiver.start()
    time.sleep(0.05)
    try:
        assert _post({"Saweria-Callback-Signature": "invalid"}) == 401
        assert receiver.get_next_donation() is None
    finally:
        receiver.stop()


def test_valid_signature_is_accepted_when_stream_key_configured():
    receiver = SaweriaReceiver(port=PORT, stream_key=STREAM_KEY, host="127.0.0.1")
    receiver.start()
    time.sleep(0.05)
    try:
        assert _post({"Saweria-Callback-Signature": _signature(_payload())}) == 200
        donation = receiver.get_next_donation()
        assert donation is not None
        assert donation["id"] == "security-test"
    finally:
        receiver.stop()


def test_receiver_defaults_to_localhost_binding():
    receiver = SaweriaReceiver(port=PORT, stream_key="")
    assert receiver.host == "127.0.0.1"


def test_unsigned_webhook_remains_compatible_without_stream_key():
    receiver = SaweriaReceiver(port=PORT, stream_key="", host="127.0.0.1")
    receiver.start()
    time.sleep(0.05)
    try:
        assert _post({}) == 200
        assert receiver.get_next_donation() is not None
    finally:
        receiver.stop()


if __name__ == "__main__":
    for name in dir():
        if name.startswith("test_"):
            globals()[name]()
    print("Saweria security tests passed")
