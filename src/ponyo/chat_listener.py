import time
import os
import sys
import threading
import queue
from .config import YOUTUBE_VIDEO_ID
from .youtube_chat_reader import YouTubeLiveChatReader

# Import GameBridge jika tersedia
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
try:
    from game_bridge import bridge
except Exception:
    bridge = None

class ChatListener:
    def __init__(self, chat_queue: queue.Queue, video_id: str = None):
        self.chat_queue = chat_queue
        # None means use .env; an explicit empty string is an offline opt-out.
        self.video_id = YOUTUBE_VIDEO_ID if video_id is None else video_id.strip()
        self.is_running = False
        self.yt_thread = None
        self.console_thread = None

    @staticmethod
    def retry_delay(retry_count: int) -> float:
        """Backoff reconnect yang dibatasi agar tidak membanjiri YouTube."""
        return min(30.0, float(2 ** max(0, int(retry_count))))

    def start(self):
        self.is_running = True
        
        # Selalu aktifkan listener console agar bisa menerima input langsung dari terminal
        self.console_thread = threading.Thread(target=self._listen_console, daemon=True)
        self.console_thread.start()

        if self.video_id and self.video_id.lower() not in ["", "none", "test"]:
            self.yt_thread = threading.Thread(target=self._listen_youtube, daemon=True)
            self.yt_thread.start()
            print(f"[CHAT] Menghubungkan ke live chat YouTube stream: {self.video_id}...")
        else:
            print("[CHAT] Mode Simulasi Aktif: Tidak ada YouTube Video ID.")
            print("[CHAT] Ketik chat penonton langsung di terminal (Contoh: 'Budi: Halo Mika')")

    def _listen_youtube(self):
        reader = YouTubeLiveChatReader(self.video_id)
        
        retry_count = 0
        while self.is_running and not reader.initialize():
            retry_count += 1
            delay = self.retry_delay(retry_count - 1)
            print(f"[CHAT] Reconnect YouTube #{retry_count}; mencoba lagi dalam {delay:.1f} detik.")
            time.sleep(delay)

        if not self.is_running:
            return
        print(f"[CHAT] Terhubung langsung ke Live Chat YouTube ({self.video_id})!")
        print("[CHAT] Bot siap mendengarkan dan merespons pesan penonton secara real-time.")

        reconnect_count = 0
        while self.is_running:
            try:
                new_msgs = reader.fetch_new_messages()
                if not reader.continuation:
                    reconnect_count += 1
                    delay = self.retry_delay(reconnect_count - 1)
                    print(f"[CHAT] Continuation YouTube terputus; reconnect dalam {delay:.1f} detik.")
                    time.sleep(delay)
                    continue
                reconnect_count = 0
                for author, message in new_msgs:
                    if not self.is_running:
                        break
                    print(f"\n[LIVE CHAT] {author}: {message}")
                    if bridge and message.startswith("!"):
                        bridge.emit_viewer_command(author, message)
                    self.chat_queue.put((author, message))
                
                time.sleep(1.5)
            except Exception as e:
                print(f"[CHAT ERROR] Gangguan saat membaca chat: {e}")
                time.sleep(3)

    def _listen_console(self):
        while self.is_running:
            try:
                line = input()
                if not line or not line.strip():
                    continue
                if ":" in line:
                    parts = line.split(":", 1)
                    author = parts[0].strip()
                    message = parts[1].strip()
                else:
                    author = "Penonton"
                    message = line.strip()

                print(f"[INPUT TERMINAL] {author}: {message}")
                if bridge and message.startswith("!"):
                    bridge.emit_viewer_command(author, message)
                self.chat_queue.put((author, message))
            except (EOFError, KeyboardInterrupt):
                break
            except Exception:
                pass

    def stop(self):
        self.is_running = False
