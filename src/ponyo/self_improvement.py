"""
SELF-IMPROVEMENT ENGINE FOR PONYO VTUBER
========================================
Modul A: Evaluasi Pasca-Streaming (Post-Stream Reflection & Diary)
Modul B: Kamus Pengalaman & Slang Baru (Dynamic Vocabulary & Slang Learning)
"""

import os
import json
import time
import re
from .config import OLLAMA_URL, OLLAMA_MODEL, OLLAMA_REQUEST_TIMEOUT
from . import ollama_runtime

PROJECT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
DATA_DIR = os.path.join(PROJECT_DIR, "data", "runtime")
os.makedirs(DATA_DIR, exist_ok=True)

DIARY_FILE = os.path.join(DATA_DIR, "ponyo_diary.json")
SLANG_FILE = os.path.join(DATA_DIR, "ponyo_slang_lexicon.json")

# =============================================================================
# MODUL B: KAMUS PENGALAMAN & SLANG BARU (DYNAMIC VOCABULARY LEARNER)
# =============================================================================

DEFAULT_SLANGS = {
    "gg": {
        "term": "GG",
        "meaning": "Good Game / permainan atau aksi yang keren banget",
        "frequency": 15,
        "sample": "Wah GG banget kamu!"
    },
    "hoki": {
        "term": "Hoki",
        "meaning": "Lagi beruntung banget / selamat dari bahaya",
        "frequency": 12,
        "sample": "Hoki parah bisa lolos dari cacing besar!"
    },
    "clutch": {
        "term": "Clutch",
        "meaning": "Momen kritis genting yang berhasil dimenangkan secara ajaib",
        "frequency": 8,
        "sample": "Aksi clutch Ponyo tadi bikin merinding!"
    },
    "turu": {
        "term": "Turu",
        "meaning": "Tidur atau istirahat",
        "frequency": 10,
        "sample": "Habis stream ini langsung turu ya!"
    },
    "mabar": {
        "term": "Mabar",
        "meaning": "Main bareng dalam game",
        "frequency": 14,
        "sample": "Kapan-kapan kita mabar lagi ya!"
    },
    "gas": {
        "term": "Gas",
        "meaning": "Ayo mulai, gaskeun, atau terus maju",
        "frequency": 16,
        "sample": "Gas terus jangan kasih kendor!"
    },
    "suhu": {
        "term": "Suhu",
        "meaning": "Pemain yang sangat jago atau master",
        "frequency": 7,
        "sample": "Ajarin Ponyo dong wahai suhu!"
    },
    "afk": {
        "term": "AFK",
        "meaning": "Away From Keyboard / sedang meninggalkan layar sejenak",
        "frequency": 6,
        "sample": "Jangan AFK dulu ya, lagi seru nih!"
    },
    "ngebug": {
        "term": "Ngebug",
        "meaning": "Ada glitch, error, atau keanehan di game",
        "frequency": 5,
        "sample": "Wah tadi cacingnya kayak ngebug ya!"
    },
    "spill": {
        "term": "Spill",
        "meaning": "Membocorkan rahasia atau menceritakan info menarik",
        "frequency": 9,
        "sample": "Coba spill tips mainnya dong!"
    }
}

class DynamicVocabularyLearner:
    def __init__(self, filepath: str = SLANG_FILE):
        self.filepath = filepath
        self.lexicon = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        # Inisialisasi awal
        self._save(DEFAULT_SLANGS)
        return dict(DEFAULT_SLANGS)

    def _save(self, data: dict = None):
        if data is None:
            data = self.lexicon
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[VOCAB ERROR] Gagal menyimpan kamus slang: {e}")

    def track_and_learn(self, text: str):
        """Catat slang, tetapi jangan gunakan istilah baru sebelum dua konfirmasi."""
        if not text:
            return

        words = re.findall(r"\b[a-zA-Z0-9_-]+\b", text.lower())
        changed = False
        for w in words:
            if w in self.lexicon:
                self.lexicon[w]["frequency"] = self.lexicon[w].get("frequency", 0) + 1
                changed = True

        match = re.search(r"\b([a-zA-Z]{2,12})\s+(?:itu|adalah|artinya|maksudnya)\s+([a-zA-Z0-9\s]{4,35})", text, re.IGNORECASE)
        if match:
            term = match.group(1).strip()
            meaning = match.group(2).strip()
            key = term.lower()
            ignored = {"apa", "siapa", "kamu", "ponyo", "layar", "game"}
            if key not in ignored and len(term) <= 12:
                item = self.lexicon.setdefault(key, {
                    "term": term.upper() if len(term) <= 4 else term.capitalize(),
                    "meaning": meaning,
                    "frequency": 0,
                    "confirmed_count": 0,
                    "confidence": 0.0,
                    "sample": text.strip(),
                })
                item["meaning"] = meaning
                item["confirmed_count"] = item.get("confirmed_count", 0) + 1
                item["confidence"] = min(1.0, 0.4 + 0.2 * item["confirmed_count"])
                item["frequency"] = item.get("frequency", 0) + 1
                changed = True

        if changed:
            self._save()

    def get_slang_context_prompt(self, message: str = None) -> str:
        """Petunjuk slang tepercaya; bila pesan tersedia, hanya istilah yang relevan."""
        if not self.lexicon:
            return ""
        from .language_naturalness import select_relevant_slangs
        if message:
            return select_relevant_slangs(message, self.lexicon)
        sorted_slangs = sorted(
            (s for s in self.lexicon.values() if float(s.get("confidence", 1.0)) >= 0.8),
            key=lambda x: x.get("frequency", 0), reverse=True
        )[:8]
        lines = [f"- {s['term']}: {s['meaning']}." for s in sorted_slangs]
        return "ISTILAH & SLANG GAMER YANG PONYO PAHAMI:\n" + "\n".join(lines) + "\n"

# =============================================================================
# MODUL A: EVALUASI PASCA-STREAMING (POST-STREAM REFLECTION & DIARY)
# =============================================================================

class PostStreamReflector:
    def __init__(self, filepath: str = DIARY_FILE, model: str = None, url: str = None):
        self.filepath = filepath
        self.model = model or OLLAMA_MODEL
        self.url = url or OLLAMA_URL
        self.diaries = self._load()

    def _load(self) -> list:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return []

    def _save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.diaries, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[DIARY ERROR] Gagal menyimpan buku harian Ponyo: {e}")

    def build_reflection_prompt(self, session_summary: dict, minutes: int = None, top_viewers_str: str = None, deaths: int = None, feasts: int = None) -> str:
        """Menyusun prompt diary dari game aktif sesi ini, bukan statistik game lama."""
        game_stats = session_summary.get("game_stats", {})
        game = session_summary.get("active_game") or game_stats.get("game") or "umum"
        minutes = minutes if minutes is not None else max(1, int(session_summary.get("session_duration_s", 0) // 60))
        viewers = session_summary.get("viewers", {})
        active = sorted(viewers.values(), key=lambda v: v.get("chat_count", 0), reverse=True)[:4]
        top_viewers_str = top_viewers_str or ", ".join(f"{v.get('display_name', 'penonton')} ({v.get('chat_count', 0)} chat)" for v in active) or "penonton setia"
        deaths = game_stats.get("deaths", 0) if deaths is None else deaths
        feasts = game_stats.get("feasts", 0) if feasts is None else feasts
        return (
            f"Streaming YouTube Ponyo baru saja selesai hari ini. Game aktif yang benar-benar dimainkan: {game}.\n"
            f"Durasi: {minutes} menit. Penonton aktif: {top_viewers_str}.\n"
            f"Statistik hanya untuk {game}: kemenangan atau momen berhasil {feasts} kali, kegagalan atau kematian {deaths} kali.\n"
            "Tuliskan catatan diary 2 sampai 3 kalimat tentang game tersebut, sebut penonton aktif, dan satu hal yang ingin Ponyo tingkatkan. "
            "Jangan mencampur nama atau statistik game lain. Gunakan nama Ponyo, bukan aku, saya, gua, atau gue."
        )

    def generate_post_stream_reflection(self, session_summary: dict) -> dict:
        """Menganalisis seluruh sesi stream yang baru selesai dan membuat refleksi buku harian"""
        if not session_summary or session_summary.get("total_chats", 0) == 0:
            print("[REFLEKSI] Sesi terlalu singkat atau belum ada chat, melewatkan evaluasi.")
            return None

        duration_sec = session_summary.get("session_duration_s", 0)
        minutes = max(1, int(duration_sec // 60))
        
        # Cari penonton paling aktif
        viewers = session_summary.get("viewers", {})
        active_viewers = sorted(viewers.values(), key=lambda v: v.get("chat_count", 0), reverse=True)[:4]
        viewer_names = [f"{v['display_name']} ({v['chat_count']} chat)" for v in active_viewers]
        top_viewers_str = ", ".join(viewer_names) if viewer_names else "penonton setia"

        # Game stats
        game_stats = session_summary.get("game_stats", {})
        deaths = game_stats.get("deaths", 0)
        feasts = game_stats.get("feasts", 0)

        prompt = self.build_reflection_prompt(session_summary, minutes, top_viewers_str, deaths, feasts)

        diary_entry_text = ""
        try:
            payload = {
                "model": self.model,
                "messages": [{"role": "user", "content": prompt}],
                "stream": False,
                "options": {
                    "temperature": 0.65,
                    "repeat_penalty": 1.2,
                    "num_predict": 85
                }
            }
            resp = ollama_runtime.post_json(
                self.model,
                "/api/chat",
                payload,
                timeout=OLLAMA_REQUEST_TIMEOUT,
            )
            if resp.status_code == 200:
                raw = resp.json().get("message", {}).get("content", "").strip()
                # Bersihkan kata ganti agar 100% konsisten 'Ponyo'
                cleaned = re.sub(r"\b(aku|saya|gua|gue)\b", "Ponyo", raw, flags=re.IGNORECASE)
                cleaned = re.sub(r"\*+", "", cleaned).strip('"\'')
                diary_entry_text = cleaned
        except Exception as e:
            print(f"[REFLEKSI] Gagal query AI untuk catatan buku harian: {e}")

        if not diary_entry_text:
            first_viewer = active_viewers[0]['display_name'] if active_viewers else "semuanya"
            diary_entry_text = f"Hari ini streaming selama {minutes} menit seru banget bareng {first_viewer}! Ponyo sempat seru-seruan main game dan ngobrol bareng di chat. Di stream berikutnya Ponyo bakal lebih lincah lagi!"

        entry = {
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "game": session_summary.get("active_game") or game_stats.get("game") or "umum",
            "duration_minutes": minutes,
            "top_viewers": [v["display_name"] for v in active_viewers],
            "total_chats": session_summary.get("total_chats", 0),
            "reflection": diary_entry_text
        }

        # Simpan ke memori permanen (maksimal 10 sesi terakhir)
        self.diaries.append(entry)
        if len(self.diaries) > 10:
            self.diaries = self.diaries[-10:]
        self._save()

        print("\n" + "=" * 60)
        print(" 📖 CATATAN BUKU HARIAN & REFLEKSI PONYO HARI INI")
        print("=" * 60)
        print(f" Waktu     : {entry['date']} ({entry['duration_minutes']} menit)")
        print(f" Penonton  : {', '.join(entry['top_viewers'])}")
        print(f" Refleksi  : \"{entry['reflection']}\"")
        print("=" * 60 + "\n")

        return entry

    def get_latest_diary_context(self) -> str:
        """Mengambil catatan refleksi stream sebelumnya untuk bahan sapaan awal"""
        if not self.diaries:
            return ""
        
        last = self.diaries[-1]
        top_str = ", ".join(last.get("top_viewers", [])[:2])
        reflection = last.get("reflection", "")
        
        ctx = (
            f"INGATAN DARI STREAM SEBELUMNYA:\n"
            f"- Di live stream kemarin, penonton paling aktif adalah: {top_str}.\n"
            f"- Catatan Ponyo kemarin: \"{reflection}\"\n"
        )
        return ctx


# =============================================================================
# MODUL C (NOMOR 6): SISTEM LEVEL & GELAR PENONTON SETIA (VIEWER LOYALTY)
# =============================================================================

LOYALTY_FILE = os.path.join(DATA_DIR, "viewer_loyalty.json")

RANK_TIERS = [
    (600, 5, "Kapten Setia Ponyo"),
    (300, 4, "Keluarga Keramat Ponyo"),
    (150, 3, "Sahabat Hantu Ponyo"),
    (50,  2, "Teman Nongkrong Ponyo"),
    (0,   1, "Teman Baru Ponyo"),
]


class ViewerLoyaltyManager:
    def __init__(self, filepath: str = LOYALTY_FILE):
        self.filepath = filepath
        self.viewers = self._load()

    def _load(self) -> dict:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    if isinstance(data, dict):
                        return data
            except Exception:
                pass
        return {}

    def _save(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.viewers, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"[LOYALTY ERROR] Gagal menyimpan data level penonton: {e}")

    @staticmethod
    def compute_rank(xp: int) -> tuple:
        for min_xp, lvl, title in RANK_TIERS:
            if xp >= min_xp:
                return lvl, title
        return 1, "Teman Baru Ponyo"

    def record_interaction(self, author: str, message: str = "", bonus_xp: int = 0) -> tuple:
        """
        Mencatat chat/interaksi penonton secara permanen lintas sesi.
        Mengembalikan (leveled_up: bool, level: int, rank_title: str)
        """
        if not author:
            return False, 1, "Teman Baru Ponyo"

        key = author.strip().lower()
        now_str = time.strftime("%Y-%m-%d %H:%M:%S")

        if key not in self.viewers:
            self.viewers[key] = {
                "display_name": author.strip(),
                "total_chats": 0,
                "xp": 0,
                "level": 1,
                "rank_title": "Teman Baru Ponyo",
                "first_seen": now_str,
                "last_seen": now_str,
                "notes": []
            }

        entry = self.viewers[key]
        old_level = entry.get("level", 1)
        entry["display_name"] = author.strip()
        entry["total_chats"] = entry.get("total_chats", 0) + 1
        entry["xp"] = entry.get("xp", 0) + 10 + bonus_xp
        entry["last_seen"] = now_str

        new_level, new_title = self.compute_rank(entry["xp"])
        entry["level"] = new_level
        entry["rank_title"] = new_title

        # Ekstrak fakta perkenalan penonton untuk diingat lintas stream
        msg_lower = (message or "").lower()
        m_city = re.search(r"\b(?:aku|saya|asal)\s+dari\s+([a-zA-Z\s]{3,20})", msg_lower)
        if m_city:
            city = m_city.group(1).strip().title()
            note = f"Asal: {city}"
            if note not in entry["notes"]:
                entry["notes"].append(note)

        m_like = re.search(r"\b(?:aku|saya)\s+(?:suka|hobi)\s+([a-zA-Z0-9\s]{3,25})", msg_lower)
        if m_like:
            fav = m_like.group(1).strip()
            note = f"Suka: {fav}"
            if note not in entry["notes"]:
                entry["notes"].append(note)

        self._save()
        leveled_up = new_level > old_level
        if leveled_up:
            print(f"[LEVEL UP!] {author} naik ke Level {new_level} ({new_title})!")
        return leveled_up, new_level, new_title

    def get_viewer_context(self, author: str) -> str:
        if not author:
            return ""
        key = author.strip().lower()
        entry = self.viewers.get(key)
        if not entry:
            return ""
        lvl = entry.get("level", 1)
        title = entry.get("rank_title", "Teman Baru Ponyo")
        chats = entry.get("total_chats", 1)
        notes = entry.get("notes", [])
        info = f"PROFIL PENONTON SETIA ({entry['display_name']}): Level {lvl} - Gelar '{title}' (Total {chats} chat)."
        if notes:
            info += f" Catatan tentang {entry['display_name']}: {', '.join(notes)}."
        return info

    def get_status_reply(self, author: str) -> str:
        key = (author or "").strip().lower()
        entry = self.viewers.get(key)
        if not entry:
            return f"Halo {author}! Kamu saat ini berada di Level 1 dengan gelar Teman Baru Ponyo! Sering-sering ngobrol bareng Ponyo supaya naik level ya!"
        lvl = entry.get("level", 1)
        title = entry.get("rank_title", "Teman Baru Ponyo")
        xp = entry.get("xp", 10)
        chats = entry.get("total_chats", 1)
        return (
            f"Wah {author}, saat ini kamu sudah Level {lvl} dengan gelar {title}! "
            f"Kamu sudah mengumpulkan {xp} poin pengalaman dari {chats} obrolan bareng Ponyo, makasih sudah setia ya!"
        )


# Instance global siap pakai
slang_learner = DynamicVocabularyLearner()
stream_reflector = PostStreamReflector()
viewer_loyalty = ViewerLoyaltyManager()
