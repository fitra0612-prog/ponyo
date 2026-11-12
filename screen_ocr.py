"""
ON-SCREEN OCR VISION ENGINE FOR PONYO VTUBER (NOMOR 5)
======================================================
Membaca teks yang tampil langsung di dalam gambar layar streaming (Display 2)
menggunakan Windows 11 Native WinRT OCR (100% Offline, Cepat, Tanpa Beban GPU).
Memungkinkan Ponyo membaca subtitle video, teks meme, skor game, atau artikel di layar!
"""

import os
import re
import time
import tempfile
import subprocess
from PIL import ImageGrab

# Area konten utama Display 2 (memotong tab browser paling atas & taskbar paling bawah)
DISP2_CONTENT_BBOX = (2060, -910, 3700, -40)


class ScreenOCREngine:
    def __init__(self):
        self.is_enabled = True
        self.last_ocr_text = ""
        self.last_ocr_time = 0.0

    def extract_screen_text(self, max_chars: int = 160) -> str:
        """Mengambil tangkapan layar area tengah Display 2 dan mengekstrak teks yang terbaca (dengan caching 7 detik)"""
        if not self.is_enabled:
            return ""

        now = time.time()
        # Optimalisasi Caching: Gunakan teks hasil OCR terakhir jika jeda belum mencapai 7 detik
        if self.last_ocr_text and (now - self.last_ocr_time < 7.0):
            return self.last_ocr_text[:max_chars]

        tmp_path = None
        try:
            img = ImageGrab.grab(bbox=DISP2_CONTENT_BBOX, all_screens=True)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tf:
                tmp_path = tf.name
            img.save(tmp_path)

            ps_script = f"""
[Console]::OutputEncoding = [System.Text.Encoding]::UTF8;
$OutputEncoding = [System.Text.Encoding]::UTF8;
Add-Type -AssemblyName System.Runtime.WindowsRuntime
$null = [Windows.Storage.StorageFile, Windows.Storage, ContentType = WindowsRuntime]
$null = [Windows.Media.Ocr.OcrEngine, Windows.Foundation, ContentType = WindowsRuntime]
$null = [Windows.Graphics.Imaging.BitmapDecoder, Windows.Foundation, ContentType = WindowsRuntime]

function Await($WinRtTask, $ResultType) {{
    $asTaskGeneric = ([System.WindowsRuntimeSystemExtensions].GetMethods() | Where-Object {{ $_.Name -eq 'AsTask' -and $_.GetParameters().Count -eq 1 -and $_.GetParameters()[0].ParameterType.Name -eq 'IAsyncOperation`1' }})[0]
    $asTask = $asTaskGeneric.MakeGenericMethod($ResultType)
    $netTask = $asTask.Invoke($null, @($WinRtTask))
    $netTask.Wait(-1) | Out-Null
    return $netTask.Result
}}

$file = Await ([Windows.Storage.StorageFile]::GetFileFromPathAsync('{tmp_path}')) ([Windows.Storage.StorageFile])
$stream = Await ($file.OpenAsync([Windows.Storage.FileAccessMode]::Read)) ([Windows.Storage.Streams.IRandomAccessStream])
$decoder = Await ([Windows.Graphics.Imaging.BitmapDecoder]::CreateAsync($stream)) ([Windows.Graphics.Imaging.BitmapDecoder])
$bitmap = Await ($decoder.GetSoftwareBitmapAsync()) ([Windows.Graphics.Imaging.SoftwareBitmap])
$engine = [Windows.Media.Ocr.OcrEngine]::TryCreateFromUserProfileLanguages()
$result = Await ($engine.RecognizeAsync($bitmap)) ([Windows.Media.Ocr.OcrResult])
Write-Output $result.Text
$stream.Dispose()
"""
            # Ambil output sebagai raw bytes (tanpa text=True) agar _readerthread tidak crash dengan cp1252
            res = subprocess.run(
                ["powershell", "-NoProfile", "-Command", ps_script],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=5,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
            )
            raw = (res.stdout or b"").decode("utf-8", errors="ignore").strip()
            cleaned = self._clean_ocr_text(raw, max_chars=max_chars)
            if cleaned:
                self.last_ocr_text = cleaned
                self.last_ocr_time = time.time()
            return cleaned
        except Exception:
            return ""
        finally:
            if tmp_path and os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass

    def _clean_ocr_text(self, raw: str, max_chars: int = 160) -> str:
        if not raw:
            return ""
        # Buang karakter non-alfanumerik aneh dan kata-kata UI standar YouTube/Browser
        text = re.sub(r"[^\w\s.,!?-]", " ", raw)
        ui_noise = {
            "subscribe", "subscribed", "share", "bagikan", "like", "dislike",
            "komentar", "comments", "live", "chat", "top", "search", "telusuri",
            "beranda", "shorts", "subscriptions", "koleksi", "history", "tonton",
            "nanti", "playlist", "more", "lainnya", "skip", "ads", "iklan"
        }
        words = []
        for w in text.split():
            if len(w) >= 3 and w.lower() not in ui_noise:
                words.append(w)

        if len(words) < 2:
            return ""
        joined = " ".join(words)
        return joined[:max_chars].strip()


screen_ocr = ScreenOCREngine()
