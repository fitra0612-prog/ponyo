"""
saweria_receiver.py - Modul Penerima & Integrasi Donasi Saweria untuk AI VTuber Ponyo.

Mendukung:
1. HTTP Webhook Server lokal (Standar resmi Saweria POST webhook) dengan validasi HMAC-SHA256 signature opsional.
2. Generator ucapan terima kasih suara TTS bertingkat (Tier 1: Boba, Tier 2: Lemari Aksesoris, Tier 3: Mahkota Sultan).
3. Pemicu otomatis efek visual display (Loncat kegirangan / Victory Dance + Konfeti + Mahkota Emas).
4. Integrasi dengan sistem loyalitas penonton (Viewer Loyalty XP).
5. Simulasi donasi lokal untuk pengetesan offline / tanpa biaya.
"""

import json
import time
import hmac
import hashlib
import threading
import queue
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Optional, Dict, Any, Tuple


def clean_text_for_ponyo(text: str) -> str:
    """Membersihkan pesan donasi dari URL, karakter aneh, emoji, dan emoticon teks"""
    if not text:
        return ""
    import re
    # Hapus URL
    cleaned = re.sub(r'https?://\S+|www\.\S+', '', text)
    # Hapus emoticon teks umum
    cleaned = re.sub(r'[:;=8][\-o\*\']?[)\](\/\\OpPdD<>3]', '', cleaned)
    cleaned = re.sub(r'[xX][dD]', '', cleaned)
    cleaned = re.sub(r'[\^~][_\-.]?[\^~]', '', cleaned)
    # Hapus karakter non-ASCII (emoji Unicode)
    cleaned = re.sub(r'[^\x00-\x7F]+', ' ', cleaned)
    # Rapikan spasi berlebih
    cleaned = " ".join(cleaned.split())
    return cleaned.strip()


class SaweriaWebhookHandler(BaseHTTPRequestHandler):
    """HTTP Request Handler untuk menangani webhook POST dari Saweria"""

    def log_message(self, format, *args):
        # Mencegah log bawaan BaseHTTPRequestHandler mengotori terminal konsol
        pass

    def do_GET(self):
        """Health check endpoint"""
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        res = json.dumps({
            "status": "online",
            "service": "Ponyo Saweria Webhook Receiver",
            "character": "Ponyo the Cute Ghost"
        }).encode("utf-8")
        self.wfile.write(res)

    def do_POST(self):
        """Menerima dan memproses payload donasi JSON dari Saweria"""
        try:
            content_length = int(self.headers.get("Content-Length", 0))
            if content_length <= 0:
                self.send_response(400)
                self.end_headers()
                return

            raw_body = self.rfile.read(content_length)
            payload_str = raw_body.decode("utf-8")
            data = json.loads(payload_str)

            # Jika stream key dikonfigurasi, signature wajib ada dan harus valid.
            # Tanpa kewajiban ini, siapa pun yang dapat menjangkau endpoint dapat
            # memalsukan donasi dan memicu TTS/animasi Ponyo.
            stream_key = self.server.receiver.stream_key
            signature = (self.headers.get("Saweria-Callback-Signature") or "").strip()

            if stream_key:
                # Format resmi: {version}{id}{amount_raw}{donator_name}{donator_email}
                version = str(data.get("version", ""))
                donation_id = str(data.get("id", ""))
                amount_raw = str(data.get("amount_raw", ""))
                donator_name = str(data.get("donator_name", ""))
                donator_email = str(data.get("donator_email", ""))

                msg_to_sign = f"{version}{donation_id}{amount_raw}{donator_name}{donator_email}"
                expected_sig = hmac.new(
                    stream_key.encode("utf-8"),
                    msg_to_sign.encode("utf-8"),
                    hashlib.sha256
                ).hexdigest()

                if not signature or not hmac.compare_digest(signature.lower(), expected_sig.lower()):
                    print(f"[SAWERIA] Peringatan: Signature webhook tidak valid atau hilang dari {self.client_address[0]}")
                    self.send_response(401)
                    self.send_header("Content-Type", "application/json")
                    self.end_headers()
                    self.wfile.write(b'{"error": "Invalid signature"}')
                    return

            # Masukkan donasi ke antrean pemrosesan
            self.server.receiver.enqueue_donation(data)

            # Respon sukses 200 OK ke server Saweria
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"status": "ok", "message": "Donation received by Ponyo"}')

        except Exception as e:
            print(f"[SAWERIA ERROR] Gagal membaca webhook POST: {e}")
            self.send_response(500)
            self.end_headers()


class SaweriaReceiver:
    """Kelas pengelola penerima donasi Saweria dan generator respon suara Ponyo"""

    def __init__(self, port: int = 49225, stream_key: str = "", host: str = "127.0.0.1"):
        self.host = (host or "127.0.0.1").strip()
        self.port = port
        self.stream_key = stream_key.strip()
        self.donation_queue = queue.Queue()
        self.server: Optional[HTTPServer] = None
        self.server_thread: Optional[threading.Thread] = None
        self.is_running = False

    def start(self):
        """Menjalankan HTTP Webhook server di background thread"""
        if self.is_running:
            return

        try:
            self.server = HTTPServer((self.host, self.port), SaweriaWebhookHandler)
            self.server.receiver = self
            self.is_running = True
            self.server_thread = threading.Thread(target=self._server_loop, daemon=True)
            self.server_thread.start()
            print("=" * 64)
            print(f"[SAWERIA] Webhook Receiver Aktif di http://localhost:{self.port}/webhook")
            if self.stream_key:
                print("[SAWERIA] Validasi Signature HMAC-SHA256: AKTIF (Stream Key Terpasang)")
            else:
                print("[SAWERIA] Validasi Signature: TERBUKA (Menerima semua payload Saweria)")
            print("=" * 64)
        except Exception as e:
            print(f"[SAWERIA ERROR] Gagal menjalankan server webhook pada port {self.port}: {e}")
            self.is_running = False

    def _server_loop(self):
        try:
            while self.is_running and self.server:
                self.server.handle_request()
        except Exception as e:
            if self.is_running:
                print(f"[SAWERIA SERVER] Exception in loop: {e}")

    def stop(self):
        """Menghentikan background server"""
        self.is_running = False
        if self.server:
            try:
                self.server.server_close()
            except Exception:
                pass
            self.server = None

    def enqueue_donation(self, raw_data: Dict[str, Any]):
        """Memasukkan data donasi mentah ke dalam queue pemrosesan"""
        donator = raw_data.get("donator_name") or raw_data.get("donator") or "Sahabat Baik"
        amount = int(raw_data.get("amount_raw") or raw_data.get("amount") or 10000)
        message = raw_data.get("message") or ""

        donation_obj = {
            "id": raw_data.get("id", str(time.time())),
            "donator": donator.strip(),
            "amount": amount,
            "message": clean_text_for_ponyo(message),
            "timestamp": time.time()
        }
        self.donation_queue.put(donation_obj)
        print(f"\n[SAWERIA MASUK] Dari: {donation_obj['donator']} | Nominal: Rp {amount:,} | Pesan: \"{donation_obj['message']}\"")

    def simulate_donation(self, donator: str = "Sultan Baik Hati", amount: int = 50000, message: str = "Semangat terus live streamnya Ponyo imut!"):
        """Simulasi pengetesan donasi lokal tanpa perlu transaksi uang nyata"""
        self.enqueue_donation({
            "id": f"sim_{int(time.time())}",
            "donator_name": donator,
            "amount_raw": amount,
            "message": message
        })

    def get_next_donation(self) -> Optional[Dict[str, Any]]:
        """Mengambil donasi berikutnya dari antrean jika ada (Non-blocking)"""
        try:
            return self.donation_queue.get_nowait()
        except queue.Empty:
            return None

    @staticmethod
    def format_speech_response(donator: str, amount: int, message: str) -> Tuple[str, str]:
        """
        Menyusun kalimat ucapan terima kasih suara TTS bertingkat (Tier 1-3)
        Returns: (speech_text, tier_name)
        """
        # Format angka dalam bahasa Indonesia
        formatted_amount = f"{amount:,}".replace(",", ".")
        clean_msg = clean_text_for_ponyo(message)

        msg_part = f"Pesan dari kakak: {clean_msg}. " if clean_msg else ""

        if amount < 50000:
            # Tier 1: Boba & Jajan Santai (< Rp 50.000)
            speech = (
                f"Wah terima kasih banyak kak {donator} atas sawerianya sebesar {formatted_amount} rupiah! "
                f"{msg_part}Rejeki nomplok buat Ponyo jajan boba manis hari ini! "
                f"Semoga rejeki kak {donator} makin lancar dan berkah selalu ya!"
            )
            tier = "TIER_1"
        elif amount < 100000:
            # Tier 2: Lemari Aksesoris / Beli Topi (Rp 50.000 - Rp 99.999)
            speech = (
                f"Asik banget! Terima kasih banyak kak {donator} atas sawerianya sebesar {formatted_amount} rupiah! "
                f"{msg_part}Ponyo senang banget, nanti bisa buat beli pita dan topi baru di lemari hantu Ponyo! "
                f"Semoga kak {donator} selalu sehat dan bahagia terus ya!"
            )
            tier = "TIER_2"
        else:
            # Tier 3: Donasi Sultan & Mahkota Emas (>= Rp 100.000)
            speech = (
                f"Waduh mata bintang Ponyo sampai berkilau! "
                f"Terima kasih banyak sultan baik hati kak {donator} atas saweria mewahnya sebesar {formatted_amount} rupiah! "
                f"{msg_part}Ini mahkota emas Ponyo persembahkan khusus buat kak {donator}! "
                f"Ponyo doakan semoga rejeki kak {donator} dilipatgandakan seribu kali lipat!"
            )
            tier = "TIER_3"

        return speech, tier
