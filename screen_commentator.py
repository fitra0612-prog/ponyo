import os
import re
import time
import random
import ctypes
from ctypes import wintypes
import requests
from collections import deque
from config import VTUBER_SYSTEM_PROMPT, OLLAMA_REQUEST_TIMEOUT, OLLAMA_MAX_ATTEMPTS, YAP_PLAYFUL_CHANCE
from ollama_runtime import ollama_runtime
from content_policy import sanitize_output
from yapping_catalog import (
    YAPPING_CATALOG,
    get_yapping_angle,
    get_fallback_yap,
    get_playful_yap,
    PLAYFUL_YAPS,
    ensure_complete_sentence
)
from screen_ocr import screen_ocr
from local_vlm import local_vlm
from visual_validation import classify_visual_context
from dungeon_slasher_knowledge import get_dungeon_slasher_context
# Set DPI awareness for multi-monitor accuracy
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)
except Exception:
    pass

user32 = ctypes.windll.user32

class ScreenCommentator:
    def __init__(self, ai_brain, yap_interval: int = 25, chess_coach=None):
        self.ai_brain = ai_brain
        self.yap_interval = yap_interval
        self.chess_coach = chess_coach
        self.last_yap_time = time.time()
        self.last_title = ""
        self.is_enabled = True
        self.recent_yaps = deque(maxlen=8)
        self.yap_cycle = 0

    def get_screen_context(self) -> str:
        """Mendeteksi judul window / konten yang sedang tampil di layar utama streaming"""
        wins = []

        def enum_proc(hwnd, lparam):
            if user32.IsWindowVisible(hwnd) and not user32.IsIconic(hwnd):
                rect = wintypes.RECT()
                user32.GetWindowRect(hwnd, ctypes.byref(rect))
                # Cek overlap dengan area monitor game (Display 2: 1920, -1036, 3840, 44)
                if rect.right > 1920 and rect.left < 3840 and rect.bottom > -1036 and rect.top < 44:
                    length = user32.GetWindowTextLengthW(hwnd)
                    if length > 0:
                        buf = ctypes.create_unicode_buffer(length + 1)
                        user32.GetWindowTextW(hwnd, buf, length + 1)
                        title = buf.value.strip()
                        # Filter window sistem / desktop / overlay / tool streaming & pengembang
                        ignored = [
                            'Program Manager', 'Windows Shell', 'Settings', 'Cua.', 
                            'Taskbar', 'Tray', 'Default IME', 'MSCTFIME',
                            'Hermes', 'Ponyo Ghost Display', 'OBS', 'OBS Studio',
                            'Command Prompt', 'Windows PowerShell', 'cmd.exe'
                        ]
                        if title and not any(title.startswith(ig) or title == ig for ig in ignored):
                            w = rect.right - rect.left
                            h = rect.bottom - rect.top
                            if w > 300 and h > 200:
                                wins.append((title, w * h))
            return True

        WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
        user32.EnumWindows(WNDENUMPROC(enum_proc), 0)

        if not wins:
            return ""

        # Ambil window paling depan (topmost Z-order) yang sedang tampil di layar
        raw_title = wins[0][0]

        # Bersihkan akhiran browser, hashtag, dan simbol agar konteks judul lebih murni
        clean = raw_title
        for suffix in [' - Brave', ' - Google Chrome', ' - Microsoft Edge', ' - Mozilla Firefox']:
            if clean.endswith(suffix):
                clean = clean[:-len(suffix)]
        clean = re.sub(r"#[a-zA-Z0-9_]+", "", clean)
        clean = re.sub(r"[^\x00-\x7F]+", " ", clean)
        clean = " ".join(clean.split()).strip()

        # Abaikan jika hanya halaman tab kosong (New Tab)
        if clean.lower() in ['new tab', 'tab baru', 'start page', 'about:blank', 'youtube']:
            return ""
        return clean

    def _is_repetitive(self, text: str) -> bool:
        if not text:
            return True
        w_new = set(text.lower().split())
        for old in self.recent_yaps:
            w_old = set(old.lower().split())
            if not w_new or not w_old:
                continue
            if len(w_new & w_old) / max(len(w_new), len(w_old)) > 0.50:
                return True
        return False

    def generate_yap(self) -> str:
        """Menghasilkan yapping layar atau celotehan playful spontan yang aman."""
        if not self.is_enabled:
            return ""

        # Tidak semua yapping harus membahas layar. Mode playful membuat Ponyo
        # terdengar seperti anak kecil yang spontan, tetapi tetap aman dan singkat.
        if random.random() < YAP_PLAYFUL_CHANCE:
            playful = sanitize_output(get_playful_yap(list(self.recent_yaps)))
            if playful and not self._is_repetitive(playful):
                playful = ensure_complete_sentence(playful)
                self.recent_yaps.append(playful)
                self.last_yap_time = time.time()
                return playful

        context_title = self.get_screen_context()
        if not context_title:
            # Tanpa layar aktif, tetap beri celotehan playful agar stream tidak kaku.
            playful = sanitize_output(get_playful_yap(list(self.recent_yaps)))
            playful = ensure_complete_sentence(playful)
            self.recent_yaps.append(playful)
            self.last_yap_time = time.time()
            return playful

        self.last_title = context_title

        # Klasifikasikan kategori layar dan ambil sudut pandang celotehan yang pas
        ocr_snippet = screen_ocr.extract_screen_text(max_chars=120)
        # Baca cache saja sebelum Qwen; refresh Moondream dijadwalkan setelah
        # prompt yapping selesai agar tidak berebut jalur inferensi.
        vlm_desc = local_vlm.get_visual_context(max_chars=140, trigger_refresh=False)
        visual_state = classify_visual_context(context_title, ocr_snippet, vlm_desc)
        category = visual_state["category"]
        category_name = YAPPING_CATALOG.get(category, {}).get("name", "Tampilan Layar")
        if visual_state.get("conflict"):
            print(f"[VISUAL] Konflik bukti layar; memakai kategori konservatif {category} dari {visual_state.get('evidence', [])}")
        # Sinkronkan game aktif ke diary; kategori layar terbaru mengalahkan konteks lama.
        memory = getattr(self.ai_brain, "memory", None)
        if memory and category in {"GAME_DUNGEON_SLASHER", "GAME_SLITHER", "GAME_GENERAL", "CHESS_GAME"}:
            memory.set_active_game(category_name)
        chosen_angle = get_yapping_angle(category, self.yap_cycle)
        current_cycle = self.yap_cycle
        self.yap_cycle += 1

        # Jika layar sedang menampilkan papan catur aktif DAN mode Chess Coach diaktifkan
        if category == "CHESS_GAME" and self.chess_coach and self.chess_coach.is_enabled:
            try:
                accurate_chess_yap = self.chess_coach.generate_accurate_board_yap(cycle=current_cycle)
                if accurate_chess_yap and not self._is_repetitive(accurate_chess_yap):
                    self.recent_yaps.append(accurate_chess_yap)
                    self.last_yap_time = time.time()
                    local_vlm.get_visual_context(trigger_refresh=True)
                    return accurate_chess_yap
            except Exception as e:
                print(f"[YAP CHESS] Fallback ke komentar umum: {e}")

        no_chess_rule = ""
        if category != "CHESS_GAME":
            no_chess_rule = "\n6. DILARANG KERAS membahas catur, pion, bidak, raja, atau skakmat karena layar saat ini TIDAK sedang menampilkan catur!"

        system_prompt = (
            "Kamu adalah Ponyo, gadis hantu kecil yang imut, ceria, dan ramah yang sedang live streaming di YouTube.\n"
            f"Aktivitas di layar saat ini: \"{context_title}\" ({category_name}).\n"
            "Aturan Berbicara (WAJIB DITAATI):\n"
            "1. HANYA komentari apa yang benar-benar tampil di layar saat ini secara alami sebagai streamer! Jangan membahas hal di luar layar dan jangan mengarang posisi petak bidak yang tidak disebut di atas.\n"
            "2. WAJIB selalu menyebut diri sendiri dengan nama 'Ponyo' (DILARANG KERAS menggunakan kata 'aku', 'saya', 'gua', atau 'gue').\n"
            "3. DILARANG KERAS menyebut nama 'Stockfish', 'engine', atau 'bot', serta jangan pernah sebut 'layar kedua' atau 'monitor kedua' (sebut 'layar Ponyo' atau 'papan catur').\n"
            "4. Langsung ucapkan kalimat komentarmu secara santai (1 sampai 2 kalimat utuh), jangan awali dengan kata kaku seperti 'Pernyataan yang ditampilkan'.\n"
            "5. Gunakan gaya lisan Ponyo yang spontan, hangat, dan imut seperti anak perempuan yang sedang ngobrol dengan teman. Reaksi kecil seperti 'Wah', 'Hehe', atau 'Ih' boleh dipakai secukupnya. Jangan menyalin gaya laporan dari VLM.\n"
            "6. Dilarang membuat daftar atau menyebut koordinat, persentase, piksel, garis horizon, ukuran, atau istilah teknis. Jangan mengarang detail yang tidak jelas.\n"
            f"7. Dilarang keras memakai emoji, emoticon teks, tanda bintang (*), atau hashtag (#).{no_chess_rule}"
        )
        if category == "GAME_DUNGEON_SLASHER":
            system_prompt += "\n\n" + get_dungeon_slasher_context(1800)

        clean_topic = context_title.replace(" - YouTube", "").strip()
        # Bukti OCR dan VLM sudah diambil untuk validasi visual di atas.
        ocr_context = f" Teks di layar: \"{ocr_snippet}\"." if ocr_snippet else ""
        vlm_context = f" Pemandangan visual di layar: \"{vlm_desc}\"." if vlm_desc else ""

        user_content = (
            f"Di layar Ponyo sekarang sedang tampil: \"{clean_topic}\".{ocr_context}{vlm_context} "
            f"{chosen_angle} (Sebut atau bahas langsung topik \"{clean_topic}\" dengan santai!)"
        )

        # Eksekusi via AI Lokal Ollama (/api/chat)
        if getattr(self.ai_brain, "is_ready", False):
            for attempt in range(OLLAMA_MAX_ATTEMPTS):
                try:
                    temp = 0.65 if attempt == 0 else 0.85
                    messages = [
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_content}
                    ]
                    payload = {
                        "model": self.ai_brain.ollama_model,
                        "messages": messages,
                        "stream": False,
                        "keep_alive": "24h",
                        "options": {
                            "temperature": temp,
                            "repeat_penalty": 1.2,
                            "num_ctx": 1024,
                            "num_predict": 120,
                        }
                    }
                    resp = ollama_runtime.post_json(
                        self.ai_brain.ollama_model,
                        "/api/chat",
                        payload,
                        timeout=OLLAMA_REQUEST_TIMEOUT,
                        lane="yapping",
                    )
                    if resp.status_code == 200:
                        raw_reply = resp.json().get("message", {}).get("content", "")
                        cleaned = sanitize_output(self.ai_brain._clean_text_for_tts(raw_reply))
                        if len(cleaned) > 220:
                            cleaned = cleaned[:220].rsplit(" ", 1)[0]
                        cleaned = ensure_complete_sentence(cleaned)
                        # Tolak jika layar bukan catur tapi AI malah menyebut istilah catur
                        if any(term in cleaned.lower() for term in ["koordinat", "persentase", "piksel", "garis horizon", "ketebalan"]):
                            continue
                        # Tolak keluaran yang masih terdengar seperti laporan teknis.
                        if cleaned.lower().startswith(("berdasarkan gambar", "pada gambar ini", "gambar ini menunjukkan")):
                            continue
                        # Tolak jika layar bukan catur tapi AI malah menyebut istilah catur
                        if category != "CHESS_GAME" and any(
                            cw in cleaned.lower() for cw in ["catur", "chess", "pion", "bidak", "skakmat", "rokade"]
                        ):
                            continue
                        if cleaned and not self._is_repetitive(cleaned):
                            self.recent_yaps.append(cleaned)
                            self.last_yap_time = time.time()
                            local_vlm.get_visual_context(trigger_refresh=True)
                            return cleaned
                except Exception as e:
                    print(f"[YAP] Error lokal Ollama: {e}")

        # Fallback offline yang variatif dan sesuai kategori layar
        fallback = self._fallback_yap(category)
        local_vlm.get_visual_context(trigger_refresh=True)
        return fallback

    def _fallback_yap(self, category: str = "CASUAL_STREAM") -> str:
        """Mengambil celotehan cadangan terkurasi sesuai kategori layar yang aktif"""
        chosen = get_fallback_yap(category, list(self.recent_yaps))
        self.recent_yaps.append(chosen)
        self.last_yap_time = time.time()
        return chosen
