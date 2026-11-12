"""
local_vlm.py - Local Vision-Language Model (VLM) Engine untuk AI VTuber Ponyo.
=============================================================================
Menggunakan model visual lokal Ollama (moondream:latest) 100% offline untuk:
1. Menangkap tangkapan layar area konten streaming (Display 2).
2. Mengekstrak deskripsi visual grafis (objek 3D, karakter game, warna, tata letak).
3. Berjalan di background thread dengan caching cerdas (TTL ~15 detik) sehingga
   TIDAK membebani atau memperlambat respon suara TTS dan animasi Pygame!
"""

import re
import time
import base64
import json
import threading
import urllib.request
import urllib.error
from io import BytesIO
from typing import Optional
from PIL import Image, ImageGrab

from config import (
    OLLAMA_URL,
    ENABLE_LOCAL_VLM,
    VLM_MODEL,
    VLM_CACHE_TTL,
    OLLAMA_REQUEST_TIMEOUT,
)
from ollama_runtime import ollama_runtime, OllamaResourceBusy
from structured_logging import structured_logger
# Area konten utama Display 2 pada host ini:
DISP2_CONTENT_BBOX = (2060, -910, 3700, -40)

# Prompt sengaja meminta bahasa percakapan agar hasil VLM tidak terdengar seperti
# laporan komputer atau pembacaan koordinat gambar.
DEFAULT_VLM_PROMPT = (
    "Lihat gambar layar ini sebagai pengamat livestream. "
    "Jawab dalam Bahasa Indonesia dengan satu kalimat pendek dan santai. "
    "Sebut hanya objek, aplikasi, game, karakter, atau suasana yang benar-benar terlihat. "
    "Jangan menyebut koordinat, persentase, garis horizon, ukuran, posisi piksel, "
    "nomor item, atau istilah teknis. Jangan mengarang detail yang tidak jelas. "
    "Jawaban harus terdengar seperti catatan singkat untuk Ponyo, bukan laporan analisis."
)


class LocalVLMEngine:
    def __init__(
        self,
        ollama_url: str = OLLAMA_URL,
        model_name: str = VLM_MODEL,
        cache_ttl: float = VLM_CACHE_TTL,
        is_enabled: bool = ENABLE_LOCAL_VLM
    ):
        self.ollama_url = ollama_url.rstrip("/")
        self.model_name = model_name
        self.cache_ttl = cache_ttl
        self.is_enabled = is_enabled

        self.last_description = ""
        self.last_update_time = 0.0
        self._lock = threading.Lock()
        self._is_analyzing = False
        self._next_retry_time = 0.0
        self._failure_backoff = 8.0
        self._busy_retry_delay = 1.0
        self._deferred_busy = False
        self.worker_runtime = None

    def set_worker_runtime(self, runtime):
        """Gunakan lane VLM terpisah jika orkestrator menyediakannya."""
        self.worker_runtime = runtime

    def is_available(self) -> bool:
        """Memeriksa apakah Ollama aktif dan memiliki model VLM yang terpasang"""
        if not self.is_enabled:
            return False
        try:
            req = urllib.request.Request(f"{self.ollama_url}/api/tags", headers={"User-Agent": "Ponyo-VLM"})
            with urllib.request.urlopen(req, timeout=2.5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                models = [m.get("name", "").split(":")[0] for m in data.get("models", [])]
                return self.model_name.split(":")[0] in models
        except Exception:
            return False

    def capture_screen_base64(self, max_width: int = 512) -> Optional[str]:
        """Mengambil screenshot Display 2 dan meresize ke resolusi ringan (~512px) untuk VLM cepat"""
        try:
            img = ImageGrab.grab(bbox=DISP2_CONTENT_BBOX, all_screens=True)
            w, h = img.size
            if w <= 0 or h <= 0:
                return None

            # Proporsional resize
            target_w = min(max_width, w)
            target_h = int(h * (target_w / w))
            img_resized = img.resize((target_w, target_h), Image.Resampling.BILINEAR)

            buf = BytesIO()
            img_resized.convert("RGB").save(buf, format="JPEG", quality=75)
            return base64.b64encode(buf.getvalue()).decode("utf-8")
        except Exception:
            # print(f"[VLM CAPTURE ERROR] {e}")
            return None

    @staticmethod
    def _humanize_description(text: str) -> str:
        """Menyaring kebocoran gaya teknis Moondream sebelum masuk ke otak/TTS."""
        cleaned = " ".join((text or "").replace("\n", " ").split())
        if not cleaned:
            return ""

        # Hilangkan format daftar yang sering dikeluarkan model visual.
        cleaned = re.sub(r"^(?:[-*]|\d+[.)])\s*", "", cleaned)

        # Moondream kadang mengeluarkan koordinat, persentase, atau laporan objek.
        # Detail tersebut tidak berguna bagi persona Ponyo dan membingungkan TTS.
        technical_patterns = (
            r"\b(?:at|around|near|located)\s+coordinates?\b",
            r"\b(?:coordinates?|koordinat)\s*[:=]?",
            r"\b\d+(?:[.,]\d+)?\s*%",
            r"\b(?:x|y)\s*[:=]\s*[-+]?\d+(?:[.,]\d+)?\b",
            r"\b(?:horizon|horizonya|pixel|pixels|piksel|persentase|percentage|percent|ketebalan)\b",
        )
        if any(re.search(pattern, cleaned, flags=re.IGNORECASE) for pattern in technical_patterns):
            return ""

        # Terjemahan ringan untuk frasa Inggris umum; model tetap diminta Bahasa Indonesia,
        # tetapi normalisasi ini mencegah bahasa Inggris mentah masuk ke TTS.
        replacements = (
            (r"^the image features?\s+", "Terlihat "),
            (r"^the image shows\s+", "Terlihat "),
            (r"^there (?:is|are)\s+", "Terlihat "),
            (r"\ba black and white striped background\b", "latar bergaris hitam putih"),
            (r"\ba colorful game character\b", "karakter game warna-warni"),
            (r"\bbackground\b", "latar"),
        )
        for pattern, replacement in replacements:
            cleaned = re.sub(pattern, replacement, cleaned, flags=re.IGNORECASE)

        # Jangan teruskan keluaran yang masih dominan berbahasa Inggris ke persona/TTS.
        # Lebih baik konteks visual kosong daripada Ponyo terdengar seperti laporan asing.
        english_markers = (" the ", " image ", " large ", " square ", " filled ", " white ", " gray ", " border ", " focus ")
        english_hits = sum(marker in f" {cleaned.lower()} " for marker in english_markers)
        if english_hits >= 2:
            return ""

        cleaned = re.sub(r"\s+", " ", cleaned).strip(" ,.;:-")
        return cleaned[:220]

    def _sync_analyze(self, prompt: str = DEFAULT_VLM_PROMPT) -> str:
        """Melakukan inferensi VLM secara synchronous ke Ollama"""
        b64_img = self.capture_screen_base64()
        if not b64_img:
            return ""

        payload = {
            "model": self.model_name,
            "prompt": prompt,
            "stream": False,
            "keep_alive": "5m",
            "images": [b64_img],
            "options": {
                "temperature": 0.2,
                "num_predict": 50
            }
        }

        try:
            resp = ollama_runtime.post_json(
                self.model_name,
                "/api/generate",
                payload,
                timeout=OLLAMA_REQUEST_TIMEOUT,
                lane="vlm",
            )
            res = resp.json()
            raw_text = res.get("response", "").strip()
            return self._humanize_description(raw_text)
        except OllamaResourceBusy:
            # Konflik antrean bukan kegagalan model. Jadwalkan percobaan singkat,
            # tanpa menandai Moondream rusak atau membuka backoff panjang.
            self._deferred_busy = True
            structured_logger.info(
                "vlm_deferred_busy",
                model=self.model_name,
                lane="vlm",
            )
            return ""
        except Exception as e:
            structured_logger.warning(
                "vlm_inference_failed",
                model=self.model_name,
                timeout=OLLAMA_REQUEST_TIMEOUT,
                error=type(e).__name__,
            )
            return ""

    def get_visual_context(self, max_chars: int = 140, trigger_refresh: bool = True) -> str:
        """
        Mengembalikan cache visual layar terkini.

        ``trigger_refresh=False`` dipakai sebelum inferensi chat/yapping agar
        refresh Moondream tidak berebut gate dengan Qwen. Pemanggil dapat
        menjadwalkan refresh setelah pekerjaan bahasa selesai.
        """
        if not self.is_enabled:
            return ""

        now = time.time()
        can_retry = now >= self._next_retry_time
        # Jika belum ada deskripsi sama sekali dan tidak sedang proses, jalankan sekali.
        if trigger_refresh and not self.last_description and not self._is_analyzing and can_retry:
            self._trigger_background_update()
            return ""

        # Jika cache sudah lewat TTL, perbarui di background.
        if trigger_refresh and (now - self.last_update_time >= self.cache_ttl) and not self._is_analyzing and can_retry:
            self._trigger_background_update()

        with self._lock:
            return self.last_description[:max_chars]

    def _trigger_background_update(self):
        """Menjalankan update visual VLM di background thread"""
        if self._is_analyzing:
            return

        def worker():
            self._is_analyzing = True
            try:
                desc = self._sync_analyze()
                if desc:
                    with self._lock:
                        self.last_description = desc
                        self.last_update_time = time.time()
                        self._next_retry_time = 0.0
                    self._deferred_busy = False
                    # print(f"[LOCAL VLM OBSERVATION]: {desc}")
                elif self._deferred_busy:
                    self._next_retry_time = time.time() + self._busy_retry_delay
                    self._deferred_busy = False
                else:
                    self._next_retry_time = time.time() + self._failure_backoff
                    structured_logger.warning("vlm_empty_result", model=self.model_name, backoff_seconds=self._failure_backoff)
            except Exception as exc:
                self._next_retry_time = time.time() + self._failure_backoff
                structured_logger.warning("vlm_worker_failed", model=self.model_name, error=type(exc).__name__, backoff_seconds=self._failure_backoff)
            finally:
                self._is_analyzing = False

        if self.worker_runtime is not None:
            if self.worker_runtime.submit("vlm", worker):
                return
        threading.Thread(target=worker, daemon=True, name="ponyo-vlm-worker").start()

    def force_refresh(self) -> str:
        """Memaksa analisa layar langsung dan mengembalikan hasilnya (blocking)"""
        if not self.is_enabled:
            return ""
        desc = self._sync_analyze()
        if desc:
            with self._lock:
                self.last_description = desc
                self.last_update_time = time.time()
        return desc


# Instance global Local VLM Engine
local_vlm = LocalVLMEngine()


if __name__ == "__main__":
    print("=== TESTING LOCAL VLM ENGINE (MOONDREAM) ===")
    vlm = LocalVLMEngine()
    avail = vlm.is_available()
    print(f"1. VLM Available in Ollama: {avail}")
    if avail:
        print("2. Capturing Display 2 and analyzing scene...")
        t0 = time.time()
        res = vlm.force_refresh()
        print(f"3. Result ({time.time() - t0:.2f}s): {res}")
        print("4. Testing Cached Non-blocking Retrieval:")
        cached = vlm.get_visual_context()
        print(f"Cached output: {cached}")
