"""
MANUAL MICROPHONE LIP-SYNC ENGINE FOR PONYO VTUBER
===================================================
Mengambil input suara dari microphone fisik secara real-time via Pygame SDL2 Audio.
Digunakan saat shortcut [V] ditekan untuk mengubah Ponyo dari bot AI otomatis
menjadi avatar VTuber manual yang dikendalikan 100% oleh suara streamer (Human VTuber).
"""

import time
import threading
import numpy as np
import pygame
import pygame._sdl2.audio as sdl2_audio
from typing import Optional, List


class MicLipSync:
    def __init__(self, threshold: float = 12.0):
        self.threshold = threshold
        self.is_active = False
        self.device: Optional[sdl2_audio.AudioDevice] = None
        self.active_device_name: Optional[str] = None
        
        # Audio metrics
        self.current_rms = 0.0
        self.smoothed_rms = 0.0
        self.noise_floor = 4.0
        self.last_sound_time = 0.0
        self.hangover_time = 0.18  # Tahan mulut terbuka 180ms agar transisi antar suku kata natural
        
        # Thread safety lock
        self._lock = threading.Lock()

    @staticmethod
    def get_available_devices() -> List[str]:
        """Mengambil daftar seluruh perangkat input mikrofon di sistem"""
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init()
            return sdl2_audio.get_audio_device_names(True)
        except Exception:
            return []

    def pick_best_device(self) -> Optional[str]:
        """Memilih mikrofon fisik terbaik secara otomatis (prioritas hardware asli)"""
        devices = self.get_available_devices()
        if not devices:
            return None

        # Prioritas 1: Realtek / Hardware Array / Built-in / USB Mic
        for d in devices:
            d_lower = d.lower()
            if any(k in d_lower for k in ["realtek", "array", "built-in", "internal", "usb", "fifine", "samson", "hyperx", "yeti", "rode"]):
                return d

        # Prioritas 2: Mikrofon fisik apapun selain software webcam virtual
        for d in devices:
            d_lower = d.lower()
            if not any(k in d_lower for k in ["iriun", "droidcam", "virtual", "cable", "obs"]):
                return d

        # Fallback: device pertama yang tersedia
        return devices[0]

    def _audio_callback(self, audiodevice, data):
        """Callback frekuensi tinggi dari SDL2 saat buffer audio mikrofon masuk"""
        try:
            samples = np.frombuffer(data, dtype=np.int16)
            if len(samples) == 0:
                return

            rms = float(np.sqrt(np.mean(samples.astype(np.float32) ** 2)))
            
            with self._lock:
                self.current_rms = rms
                # Exponential Moving Average untuk menghaluskan fluktuasi
                self.smoothed_rms = 0.55 * self.smoothed_rms + 0.45 * rms
                
                # Deteksi suara manusia di atas ambang batas (threshold)
                if self.smoothed_rms > self.threshold:
                    self.last_sound_time = time.time()
        except Exception:
            pass

    def start(self, device_name: Optional[str] = None) -> bool:
        """Memulai capture audio dari mikrofon fisik"""
        if self.is_active and self.device:
            return True

        if not device_name:
            device_name = self.pick_best_device()

        if not device_name:
            print("[MIC LIP-SYNC] Tidak ada perangkat mikrofon yang ditemukan!")
            return False

        try:
            self.active_device_name = device_name
            self.device = sdl2_audio.AudioDevice(
                device_name,
                True,                  # iscapture = True (Microphone)
                44100,                 # frequency
                pygame.AUDIO_S16SYS,   # 16-bit signed format
                1,                     # mono channel
                1024,                  # chunksize
                0,                     # allowed_changes
                self._audio_callback
            )
            self.device.pause(0)       # unpause (mulai merekam)
            self.is_active = True
            self.last_sound_time = 0.0
            self.smoothed_rms = 0.0
            print(f"[MIC LIP-SYNC] Mikrofon aktif: {device_name}")
            return True
        except Exception as e:
            print(f"[MIC LIP-SYNC] Gagal membuka mikrofon ({device_name}): {e}")
            self.is_active = False
            self.device = None
            return False

    def stop(self):
        """Menghentikan capture audio dan melepaskan perangkat mikrofon"""
        if not self.is_active and not self.device:
            return

        try:
            if self.device:
                self.device.pause(1)
                self.device.close()
        except Exception:
            pass
        finally:
            self.device = None
            self.is_active = False
            self.smoothed_rms = 0.0
            print("[MIC LIP-SYNC] Mikrofon dimatikan.")

    def toggle(self) -> bool:
        """Toggle antara aktif (Human VTuber) dan nonaktif (AI Bot)"""
        if self.is_active:
            self.stop()
            return False
        else:
            return self.start()

    def is_speaking(self) -> bool:
        """Mengembalikan True jika streamer sedang berbicara di mikrofon (mulut terbuka)"""
        if not self.is_active:
            return False
        return (time.time() - self.last_sound_time) < self.hangover_time

    def get_level(self) -> float:
        """Mengembalikan tingkat volume ternormalisasi (0.0 s.d 1.0) untuk visualisasi meter suara"""
        if not self.is_active:
            return 0.0
        # Normalisasi ke skala 0.0 - 1.0 dengan batas atas 60 RMS
        return min(1.0, max(0.0, self.smoothed_rms / 60.0))


# Global instance
mic_lip_sync = MicLipSync()
