"""
SESSION MEMORY (MEMORI SEMENTARA)
=================================
Menyimpan riwayat obrolan dan ingatan penonton HANYA selama sesi Ponyo berjalan (di RAM).
Begitu program dihentikan atau ditutup, seluruh memori otomatis ter-reset / terhapus bersih.
"""

import time
import re
from collections import deque

class SessionMemory:
    def __init__(self, max_history: int = 6):
        self.max_history = max_history
        self.session_start_time = time.time()
        
        # Riwayat obrolan terkini di RAM (maksimal 6 percakapan terakhir)
        self.dialogues = deque(maxlen=max_history)
        
        # Log lengkap sesi berjalan untuk refleksi pasca-streaming
        self.all_incoming_chats = []
        self.full_session_dialogues = []

        # Catatan penonton di sesi ini: key = author.lower()
        self.viewers = {}
        
        # Statistik sesi game berjalan
        self.game_stats = {
            "game": "umum",
            "deaths": 0,
            "feasts": 0,
            "rounds": 1
        }
        self.active_game = "umum"
        self.game_history = []
        print("[MEMORI] Sistem memori sementara sesi aktif (Hanya di RAM, auto-reset saat ditutup).")

    def set_active_game(self, game_name: str):
        """Mengunci konteks game aktif agar diary tidak mencampur game lama."""
        game = " ".join((game_name or "umum").split()).strip() or "umum"
        if game != self.active_game:
            self.game_history.append({"game": game, "time": time.time()})
        self.active_game = game
        self.game_stats["game"] = game

    def record_chat(self, author: str, message: str):
        """Mencatat aktivitas penonton di sesi ini dan mengekstrak info sederhana jika ada"""
        if not author:
            return
        
        key = author.strip().lower()
        now = time.time()
        
        self.all_incoming_chats.append({
            "author": author.strip(),
            "message": message.strip(),
            "time": now
        })

        if key not in self.viewers:
            self.viewers[key] = {
                "display_name": author.strip(),
                "chat_count": 1,
                "first_seen": now,
                "last_seen": now,
                "notes": [],
                "profile": {"name": "", "location": "", "interests": []},
                "topics": {},
                "sentiment": {"positive": 0, "neutral": 0, "negative": 0},
            }
        else:
            self.viewers[key]["chat_count"] += 1
            self.viewers[key]["last_seen"] = now
            self.viewers[key].setdefault("profile", {"name": "", "location": "", "interests": []})
            self.viewers[key].setdefault("topics", {})
            self.viewers[key].setdefault("sentiment", {"positive": 0, "neutral": 0, "negative": 0})

        viewer_entry = self.viewers[key]
        lowered = message.lower()
        for topic, words in {
            "game": ("game", "main", "mabar", "boss", "level", "catur", "cacing"),
            "stream": ("stream", "live", "ponyo", "chat"),
            "music": ("lagu", "musik", "nyanyi"),
        }.items():
            if any(word in lowered for word in words):
                viewer_entry["topics"][topic] = viewer_entry["topics"].get(topic, 0) + 1
        if any(word in lowered for word in ("bagus", "seru", "keren", "suka", "mantap", "semangat")):
            viewer_entry["sentiment"]["positive"] += 1
        elif any(word in lowered for word in ("sedih", "kecewa", "gagal", "marah")):
            viewer_entry["sentiment"]["negative"] += 1
        else:
            viewer_entry["sentiment"]["neutral"] += 1

        # Deteksi info perkenalan sederhana yang dikatakan penonton
        msg_lower = message.lower()
        viewer_entry = self.viewers[key]

        # Contoh: "namaku ryan", "nama saya ryan", "panggil aku ryan"
        m_name = re.search(r"\b(?:nama\s*(?:ku|saya)|panggil\s*aku)\s*(?:adalah|:)?\s*([a-zA-Z0-9_]+)", msg_lower)
        if m_name:
            name_value = m_name.group(1).capitalize()
            viewer_entry["profile"]["name"] = name_value
            fact = f"Nama: {name_value}"
            if fact not in viewer_entry["notes"]:
                viewer_entry["notes"].append(fact)

        # Contoh: "aku dari bandung", "tinggal di jakarta"
        m_loc = re.search(r"\b(?:dari|tinggal\s*di)\s+([a-zA-Z]+)", msg_lower)
        if m_loc:
            loc = m_loc.group(1).strip().capitalize()
            if loc.lower() not in ['sana', 'sini', 'tadi', 'mana', 'situ']:
                viewer_entry["profile"]["location"] = loc
                fact = f"Asal: {loc}"
                if fact not in viewer_entry["notes"]:
                    viewer_entry["notes"].append(fact)

        # Contoh: "aku suka mie ayam", "hobi main gitar"
        m_like = re.search(r"\b(?:suka|hobi|favorit(?:ku)?)\s+([a-zA-Z0-9_\s]{2,15})", msg_lower)
        if m_like:
            like = m_like.group(1).strip()
            fact = f"Suka: {like}"
            if like not in viewer_entry["profile"]["interests"] and len(viewer_entry["profile"]["interests"]) < 5:
                viewer_entry["profile"]["interests"].append(like)
            if fact not in viewer_entry["notes"] and len(viewer_entry["notes"]) < 5:
                viewer_entry["notes"].append(fact)

    def get_viewer_profile(self, author: str) -> dict:
        """Mengembalikan profil terstruktur penonton tanpa data sensitif."""
        key = (author or "").strip().lower()
        viewer = self.viewers.get(key)
        if not viewer:
            return {}
        return {
            "display_name": viewer.get("display_name", author),
            "chat_count": viewer.get("chat_count", 0),
            "first_seen": viewer.get("first_seen"),
            "last_seen": viewer.get("last_seen"),
            "profile": dict(viewer.get("profile", {})),
            "topics": dict(viewer.get("topics", {})),
            "sentiment": dict(viewer.get("sentiment", {})),
        }

    def record_reply(self, author: str, user_message: str, ponyo_reply: str):
        """Menyimpan pasangan tanya-jawab terakhir ke dalam memori sesi"""
        entry = {
            "author": author.strip(),
            "user_msg": user_message.strip(),
            "ponyo_reply": ponyo_reply.strip(),
            "time": time.time()
        }
        self.dialogues.append(entry)
        self.full_session_dialogues.append(entry)

    def get_session_summary_data(self) -> dict:
        """Mengambil data riwayat lengkap sesi ini untuk modul refleksi pasca-streaming"""
        return {
            "session_duration_s": time.time() - self.session_start_time,
            "total_chats": len(self.all_incoming_chats),
            "total_dialogues": len(self.full_session_dialogues),
            "viewers": dict(self.viewers),
            "dialogues": list(self.full_session_dialogues),
            "active_game": self.active_game,
            "game_history": list(self.game_history),
            "game_stats": dict(self.game_stats)
        }

    def record_game_event(self, event_type: str):
        """Mencatat statistik gameplay di sesi ini"""
        if event_type == "DEATH":
            self.game_stats["deaths"] += 1
            self.game_stats["rounds"] += 1
        elif event_type == "FEAST":
            self.game_stats["feasts"] += 1

    def get_memory_context_prompt(self, current_author: str) -> str:
        """Menghasilkan rangkuman memori sementara dalam Bahasa Indonesia untuk AI"""
        context_parts = []
        
        # 1. Profil terstruktur penonton yang sedang chat
        key = current_author.strip().lower() if current_author else ""
        if key in self.viewers:
            v = self.viewers[key]
            count = v["chat_count"]
            if count > 1:
                context_parts.append(f"- Penonton '{v['display_name']}' sudah chat {count} kali di stream ini.")
            if v.get("notes"):
                notes_str = ", ".join(v["notes"][:5])
                context_parts.append(f"- Catatan tentang {v['display_name']}: {notes_str}.")
            profile = v.get("profile", {})
            if profile.get("interests"):
                context_parts.append(f"- Minat {v['display_name']}: {', '.join(profile['interests'][:3])}.")
            topics = v.get("topics", {})
            if topics:
                context_parts.append(f"- Topik yang sering dibahas: {', '.join(sorted(topics, key=topics.get, reverse=True)[:3])}.")

        # 2. Ringkasan topik chat penonton terkini
        if self.dialogues:
            history_lines = []
            for d in list(self.dialogues)[-2:]:
                history_lines.append(f"- {d['author']} sempat chat: \"{d['user_msg']}\"")
            context_parts.append("- Topik chat penonton sebelumnya:\n  " + "\n  ".join(history_lines))

        # 3. Statistik game sesi ini jika relevan
        if self.game_stats["deaths"] > 0:
            context_parts.append(f"- Sesi game saat ini: Ronde ke-{self.game_stats['rounds']}, sempat kalah {self.game_stats['deaths']} kali.")

        if context_parts:
            return "Konteks sesi obrolan saat ini:\n" + "\n".join(context_parts) + "\n\n"
        return ""

    def clear(self):
        """Mereset seluruh memori ke kondisi awal"""
        self.dialogues.clear()
        self.all_incoming_chats.clear()
        self.full_session_dialogues.clear()
        self.viewers.clear()
        self.game_stats = {"game": "umum", "deaths": 0, "feasts": 0, "rounds": 1}
        self.active_game = "umum"
        self.game_history.clear()
        print("[MEMORI] Seluruh memori sementara sesi berhasil dibersihkan / di-reset.")
