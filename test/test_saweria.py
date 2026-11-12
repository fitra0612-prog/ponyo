"""
test_saweria.py - Skrip pengetesan integrasi Saweria untuk AI VTuber Ponyo.
Dapat digunakan untuk mengirim donasi simulasi lokal ke HTTP Webhook Receiver.

Penggunaan:
    .venv/Scripts/python.exe test_saweria.py
    .venv/Scripts/python.exe test_saweria.py --name "Sultan Budi" --amount 100000 --message "Semangat live streamnya Ponyo!"
"""

import argparse
import json
import urllib.request
import urllib.error
from config import SAWERIA_PORT, SAWERIA_STREAM_KEY
import hmac
import hashlib


def send_test_donation(donator_name: str, amount: int, message: str, port: int = SAWERIA_PORT, stream_key: str = SAWERIA_STREAM_KEY):
    url = f"http://localhost:{port}/webhook"
    payload = {
        "version": "2022.01",
        "id": f"test_{donator_name.lower().replace(' ', '_')}",
        "type": "donation",
        "amount_raw": amount,
        "cut": int(amount * 0.05),
        "donator_name": donator_name,
        "donator_email": f"{donator_name.lower().replace(' ', '')}@example.com",
        "donator_is_user": True,
        "message": message
    }

    data_bytes = json.dumps(payload).encode("utf-8")
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "Saweria-Test-Runner/1.0"
    }

    # Jika stream key diatur, tambahkan signature resmi HMAC-SHA256
    if stream_key:
        msg_to_sign = f"{payload['version']}{payload['id']}{payload['amount_raw']}{payload['donator_name']}{payload['donator_email']}"
        sig = hmac.new(stream_key.encode("utf-8"), msg_to_sign.encode("utf-8"), hashlib.sha256).hexdigest()
        headers["Saweria-Callback-Signature"] = sig

    req = urllib.request.Request(url, data=data_bytes, headers=headers, method="POST")

    print("\n" + "=" * 58)
    print(f"🚀 MENGIRIM DONASI SIMULASI SAWERIA KE http://localhost:{port}")
    print(f"• Donatur : {donator_name}")
    print(f"• Nominal : Rp {amount:,}")
    print(f"• Pesan   : \"{message}\"")
    print("=" * 58)

    try:
        with urllib.request.urlopen(req, timeout=5) as response:
            res_body = response.read().decode("utf-8")
            print(f"✅ Status Response : HTTP {response.status}")
            print(f"📄 Response Server  : {res_body}")
            print("\nDonasi berhasil dikirim! Ponyo akan merespons dengan animasi & suara.")
            return 200 <= response.status < 300
    except (urllib.error.URLError, OSError) as e:
        print(f"❌ Gagal terhubung ke receiver: {e}")
        print("Pastikan live stream Ponyo (main.py) sedang berjalan di terminal lain!")
        return False




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Test Saweria Webhook for Ponyo VTuber")
    parser.add_argument("--name", default="Sultan Budi", help="Nama donatur")
    parser.add_argument("--amount", type=int, default=50000, help="Jumlah donasi dalam Rupiah")
    parser.add_argument("--message", default="Semangat terus live streamnya Ponyo imut!", help="Pesan donasi")
    parser.add_argument("--port", type=int, default=SAWERIA_PORT, help="Port Webhook receiver")

    args = parser.parse_args()
    success = send_test_donation(args.name, args.amount, args.message, port=args.port)
    raise SystemExit(0 if success else 1)
