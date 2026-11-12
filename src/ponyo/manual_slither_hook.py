"""
MANUAL SLITHER INTERACTIVE HOOK (OPTION #3)
===========================================
Memungkinkan Streamer bermain Slither.io secara MANUAL menggunakan Mouse 100%,
sementara penonton di Live Chat YouTube dapat mengusili / membantu streamer
dengan memencet tombol SPASI (Turbo Boost) secara nyata di browser game!

Perintah Chat:
- !boost / !turbo / !ngebut / !cepat / !lari  -> Memencet Spasi selama 1.8 detik
- !rem / !stop / !lepas                       -> Melepas Spasi seketika
"""

import ctypes
import time
import threading

user32 = ctypes.windll.user32
VK_SPACE = 0x20
KEYEVENTF_KEYUP = 0x0002

class ManualSlitherHook:
    def __init__(self, boost_duration: float = 1.8, cooldown: float = 2.5):
        self.boost_duration = boost_duration
        self.cooldown = cooldown
        self.last_boost_time = 0.0
        self.is_enabled = True
        self.is_boosting = False
        self._lock = threading.Lock()

    def handle_command(self, author: str, command: str) -> bool:
        """Memproses perintah penonton dan menekan tombol fisik game jika diaktifkan"""
        if not self.is_enabled:
            return False

        cmd = command.strip().lower()
        now = time.time()

        # 1. Perintah TURBO BOOST
        if any(k in cmd for k in ["!boost", "!turbo", "!ngebut", "!cepat", "!lari", "!speed"]):
            with self._lock:
                if now - self.last_boost_time < self.cooldown:
                    sisa = self.cooldown - (now - self.last_boost_time)
                    print(f"[INTERAKTIF MANUAL] Turbo sedang cooldown ({sisa:.1f} detik lagi).")
                    return False
                self.last_boost_time = now

            def _boost_worker():
                self.is_boosting = True
                print(f"\n[INTERAKTIF MANUAL ⚡] {author} MENGAKTIFKAN TURBO BOOST SELAMA {self.boost_duration} DETIK!")
                try:
                    user32.keybd_event(VK_SPACE, 0, 0, 0) # Tekan Spasi (Turbo ON)
                    time.sleep(self.boost_duration)
                finally:
                    user32.keybd_event(VK_SPACE, 0, KEYEVENTF_KEYUP, 0) # Lepas Spasi (Turbo OFF)
                    self.is_boosting = False
                    print("[INTERAKTIF MANUAL] Turbo boost dilepas kembali.")

            threading.Thread(target=_boost_worker, daemon=True).start()
            return True

        # 2. Perintah REM / LEPAS DARURAT
        elif any(k in cmd for k in ["!rem", "!stop", "!lepas", "!brake"]):
            try:
                user32.keybd_event(VK_SPACE, 0, KEYEVENTF_KEYUP, 0)
                self.is_boosting = False
                print(f"[INTERAKTIF MANUAL] Rem darurat dari {author}: Spasi langsung dilepas!")
                return True
            except Exception:
                return False

        return False

    def toggle(self) -> bool:
        """Nyalakan / matikan mode interaktif manual via hotkey [M]"""
        self.is_enabled = not self.is_enabled
        # Lepas spasi saat dimatikan agar tidak tertahan
        if not self.is_enabled:
            user32.keybd_event(VK_SPACE, 0, KEYEVENTF_KEYUP, 0)
            self.is_boosting = False
        status = "AKTIF" if self.is_enabled else "NONAKTIF"
        print(f"[INTERAKTIF MANUAL] Kontrol Chat ke Spasi Game: {status}")
        return self.is_enabled
