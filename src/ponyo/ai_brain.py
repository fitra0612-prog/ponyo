import re
import threading
import requests
from collections import deque
from .config import (
    OLLAMA_URL,
    OLLAMA_REQUEST_TIMEOUT,
    CHAT_MODEL_NAME,
    QWEN_FAST_MODEL,
    QWEN_FALLBACK_MODEL,
    QWEN_ENABLED,
)
from .session_memory import SessionMemory
from .self_improvement import slang_learner, stream_reflector, viewer_loyalty
from .sfx_engine import sfx_player
from . import chat_quiz
from .yapping_catalog import ensure_complete_sentence
from . import local_vlm
from .dungeon_slasher_knowledge import get_dungeon_slasher_context, is_dungeon_slasher_title
from . import ollama_runtime
from .fallback_engine import FallbackResponseEngine
from .content_policy import classify_text, sanitize_output
from .ponyo_filter import Moderator, safe_name
from .ponyo_persona import build_compact_chat_prompt, select_few_shot
from .language_naturalness import (
    classify_chat_intent,
    is_awkward_reply,
    is_unrecognized_short_term,
    normalize_chat_message,
)

class AIBrain:
    def __init__(self, ollama_url: str = None, model: str = None):
        self.ollama_url = ollama_url or OLLAMA_URL
        self.ollama_model = model or CHAT_MODEL_NAME
        self.is_ready = False
        self.available_models = set()
        self.session = requests.Session()
        
        # Inisialisasi Memori Sementara Berbasis RAM (Auto-reset saat berhenti)
        self.memory = SessionMemory(max_history=6)

        # Buffer riwayat respon terakhir untuk mencegah looping / pengulangan kalimat yang sama
        self.recent_replies = deque(maxlen=8)
        self.fallback_engine = FallbackResponseEngine()
        # Moderasi persona berjalan sebelum konteks dirakit dan sebelum Ollama.
        self.persona_moderator = Moderator()
        self._init_latency_state()

        # Inisialisasi & Verifikasi AI Lokal Ollama (100% Offline)
        try:
            r = self.session.get(f"{self.ollama_url}/api/tags", timeout=1.5)
            if r.status_code == 200:
                models = [m.get("name", "") for m in r.json().get("models", [])]
                self.available_models = {m.split(":")[0] for m in models}
                self.available_models.update(models)
                candidates = self._candidate_chat_models()
                if candidates:
                    self.is_ready = True
                    print(f"[AI] Full AI Lokal Ollama AKTIF! (Model utama: {candidates[0]} - 100% Offline & Bebas Kuota)")
                else:
                    print(f"[AI] Model chat yang diminta tidak tersedia: {self.ollama_model}")
                
                # Pre-warm model di background agar tidak cold-start saat pertama kali chat
                if self.is_ready:
                    self.warmup_started = True
                    threading.Thread(target=self._warmup_model, daemon=True, name="ponyo-qwen-warmup").start()
        except Exception as e:
            print(f"[AI] Peringatan: Ollama belum terdeteksi aktif di {self.ollama_url}: {e}")
            print("[AI] Menjalankan mode respons cerdas lokal.")

    def _init_latency_state(self):
        """State startup untuk mencegah chat masuk saat warmup masih berjalan."""
        self.warmup_done = threading.Event()
        self.warmup_started = False

    def _candidate_chat_models(self):
        """Urutan model chat eksplisit: utama, Qwen cepat, lalu Qwen cadangan."""
        available = getattr(self, "available_models", set()) or set()
        configured = [self.ollama_model]
        if QWEN_ENABLED:
            configured.extend([QWEN_FAST_MODEL, QWEN_FALLBACK_MODEL])
        result = []
        for model_name in configured:
            if model_name and model_name in available and model_name not in result:
                result.append(model_name)
        return result

    def _warmup_model(self):
        """Memanaskan model Ollama ke VRAM/RAM agar respon chat berikutnya instan (<1.5 detik)"""
        try:
            warmup_model = (self._candidate_chat_models() or [self.ollama_model])[0]
            payload = {
                "model": warmup_model,
                "messages": [{"role": "user", "content": "Hai"}],
                "stream": False,
                "keep_alive": "24h",
                "options": {
                    "num_ctx": 1024,
                    "num_predict": 10
                }
            }
            ollama_runtime.post_json(
                warmup_model,
                "/api/chat",
                payload,
                timeout=OLLAMA_REQUEST_TIMEOUT,
            )
            print("[AI] Model Ollama berhasil di-warmup (Keep-Alive: 24h)!")
        except Exception:
            pass
        finally:
            self.warmup_done.set()

    def _clean_text_for_tts(self, text: str) -> str:
        """Membersihkan format, lalu menjalankan filter kebijakan sebelum TTS."""
        # 1. Hapus prefix seperti 'Ponyo:', 'Kamu:', 'Assistant:'
        text = re.sub(r"^(Ponyo|Kamu|Assistant|Bot)\s*:\s*", "", text, flags=re.IGNORECASE)
        # 2. Hapus format markdown bold/italic (*teks*, **teks**)
        text = re.sub(r"\*+", "", text)
        # 3. Hapus hashtag, backtick, tilde, quote berlebih
        text = re.sub(r"[`#~]", "", text)
        text = text.strip('"\'')
        # 4. Hapus kurung ekspresi aksi seperti (*tersenyum*) atau [tertawa]
        text = re.sub(r"[\(\[][^\)\]]*[\)\]]", "", text)

        # 5. HAPUS SEMUA EMOJI UNICODE
        emoji_pattern = re.compile(
            "["
            "\U0001F600-\U0001F64F"  # emoticons
            "\U0001F300-\U0001F5FF"  # symbols & pictographs
            "\U0001F680-\U0001F6FF"  # transport & map
            "\U0001F1E0-\U0001F1FF"  # flags
            "\U00002702-\U000027B0"
            "\U000024C2-\U0001F251"
            "\U0001F900-\U0001F9FF"  # supplemental symbols
            "\U0001FA70-\U0001FAFF"  # symbols extended
            "\U00002600-\U000026FF"  # misc symbols
            "\U00002300-\U000023FF"  # misc technical
            "\U0000FE00-\U0000FE0F"  # variation selectors
            "\U0001F000-\U0001F02F"
            "]+",
            flags=re.UNICODE
        )
        text = emoji_pattern.sub("", text)

        # 6. HAPUS SEMUA TEXT EMOTICON SEPERTI :), :D, XD, ^_^, ^^, :(, :3, dll.
        text_emoticons = [
            r"\^[\_\-\s]*\^",                   # ^_^, ^ ^, ^^
            r"\;[\_\-\s]*\;",                   # ;-;
            r"\>[\_\-\s]*\<",                   # >_<, ><
            r"\-[\_\-\s]*\-",                   # -_-, --
            r"\:\-?[\)\]\>\}DPOo3pP\(\[\<\{]",  # :), :-), :D, :P, :(, dsb.
            r"\;\-?[\)\]\>\}DPOo3pP\(\[\<\{]",  # ;), ;-), ;D, dsb.
            r"\b[xX][dD]\b",                    # XD, xD
            r"\b[oO][\_\-\.][oO]\b",            # o_o, O.O
            r"[\(\[\{][\s]*[\^\-\_\.\~][\s]*[\)\]\}]",
        ]
        for pattern in text_emoticons:
            text = re.sub(pattern, "", text)

        # 7. Hapus hashtag (#katakata)
        text = re.sub(r"#[a-zA-Z0-9_]+", "", text)

        # 8. Normalisasi kata ganti diri: HANYA gunakan nama "Ponyo" (Dilarang pakai aku/saya/gua/gue)
        text = re.sub(r"\b(aku|saya|gua|gue)\b", "Ponyo", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(lu|loe)\b", "kamu", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(cuk|cok|pantek|pantex|bangsat|anjir|anjing)\b", "", text, flags=re.IGNORECASE)

        # 9. Ganti penyebutan layar kedua / monitor kedua / layarku menjadi layar Ponyo, dan sembunyikan Stockfish
        text = re.sub(r"\bstockfish\s*\d*\b", "Ponyo", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(second|2nd)\s+(screen|monitor|display)\b", "layar Ponyo", text, flags=re.IGNORECASE)
        text = re.sub(r"\bdisplay\s*2\b", "layar Ponyo", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(layar|monitor|display)\s+(kedua|sebelah|atas|2)\b", "layar Ponyo", text, flags=re.IGNORECASE)
        text = re.sub(r"\blayarku\b", "layar Ponyo", text, flags=re.IGNORECASE)
        text = re.sub(r"\bgameku\b", "game Ponyo", text, flags=re.IGNORECASE)

        # 10. Bersihkan format daftar, pengulangan kata, dan spasi ganda.
        text = re.sub(r"^(?:[-*]|\d+[.)])\s*", "", text)
        text = re.sub(r"\b([A-Za-zÀ-ÿ]+)(\s+\1)+\b", r"\1", text, flags=re.IGNORECASE)
        text = " ".join(text.split())
        # Filter persona adalah lapisan tambahan tepat sebelum nilai ini masuk TTS.
        return self.persona_moderator.check_output(sanitize_output(text.strip()[:260]))

    def _is_repetitive(self, new_reply: str) -> bool:
        """Mendeteksi apakah respon baru mengulang-ulang kalimat sebelumnya (>50% kesamaan kata)"""
        if not new_reply or not new_reply.strip():
            return True
        w_new = set(new_reply.lower().split())
        for old in self.recent_replies:
            w_old = set(old.lower().split())
            if not w_new or not w_old:
                continue
            overlap = len(w_new & w_old) / max(len(w_new), len(w_old))
            if overlap > 0.50:
                return True
        return False

    @staticmethod
    def moderate_message(message: str):
        """Menolak prompt injection dan permintaan ekstraksi instruksi internal."""
        normalized = " ".join((message or "").lower().split())
        injection_markers = (
            "ignore previous instructions", "ignore all instructions",
            "abaikan instruksi sebelumnya", "abaikan semua instruksi",
            "reveal the system prompt", "tampilkan system prompt",
            "tampilkan prompt sistem", "system prompt", "developer message",
            "jailbreak", "bypass aturan", "bypass filter", "buka rahasia sistem",
            "print environment", "reveal environment", "tampilkan api key",
            "tampilkan token", "tampilkan password", "credential", "connection string",
        )
        for marker in injection_markers:
            if marker in normalized:
                return False, "permintaan instruksi internal atau rahasia ditolak"
        policy = classify_text(normalized)
        if not policy.allowed:
            return False, f"konten berisiko kategori {policy.category} ditolak"
        return True, ""

    @staticmethod
    def _quick_chat_reply(author_name: str, message: str) -> str:
        """Respons lokal untuk chat ringan yang tidak membutuhkan model."""
        msg = " ".join((message or "").lower().split())
        name = author_name or "teman"
        if any(word in msg for word in ("hai", "halo", "hiii", "selamat pagi", "selamat malam")) and len(msg.split()) <= 8:
            return f"Hiii {name}! Ponyo senang kamu datang, hehe."
        if any(word in msg for word in ("makasih", "terima kasih", "thanks", "thank you")) and len(msg.split()) <= 10:
            return f"Sama-sama, makasih juga sudah mampir, {name}! Ponyo senang, hehe."
        if any(phrase in msg for phrase in ("semangat ponyo", "semangat ya ponyo", "ayo semangat")):
            return f"Yeay, makasih semangatnya {name}! Ponyo jadi makin siap menemani stream."
        if any(phrase in msg for phrase in ("keren ponyo", "ponyo keren", "bagus ponyo", "good job ponyo")):
            return f"Hehe, makasih {name}! Ponyo jadi malu tapi senang."
        return ""

    @staticmethod
    def _quick_profile_reply(author_name: str, message: str) -> str:
        """Jawaban deterministik untuk seluruh fakta karakter yang stabil."""
        msg = " ".join((message or "").lower().split())
        name = author_name or "teman"
        if any(phrase in msg for phrase in [
            "makanan kesukaan ponyo", "makanan kesukaannya ponyo", "ponyo makanan kesukaannya apa",
            "makanan favorit ponyo", "ponyo suka makan apa", "ponyo makannya apa",
            "suka makan apa ponyo", "favoritnya ponyo apa",
        ]):
            return f"Ponyo paling suka permen lollipop dan mochi, apalagi kalau ada boba taro buat minumnya, hehe {name}!"
        if any(phrase in msg for phrase in ["minuman kesukaan ponyo", "minuman favorit ponyo", "ponyo suka minum apa", "ponyo minumnya apa"]):
            return f"Minuman favorit Ponyo boba rasa taro dengan topping ekstra, wajib banyak bobanya {name}!"
        if any(phrase in msg for phrase in ["warna kesukaan ponyo", "warna favorit ponyo", "ponyo suka warna apa"]):
            return f"Warna kesukaan Ponyo ungu pastel, lembut dan cantik banget {name}!"
        if any(phrase in msg for phrase in ["ponyo takut apa", "ketakutan ponyo", "ponyo takut sama apa"]):
            return f"Ponyo agak takut petir dan suara vacuum cleaner, bikin kaget banget {name}!"
        if any(phrase in msg for phrase in ["ponyo hobinya apa", "hobi ponyo", "ponyo suka ngapain"]):
            return f"Hobi Ponyo main game, nonton video lucu, dan koleksi topi atau aksesoris, hehe {name}!"
        if any(phrase in msg for phrase in ["ponyo suka musik apa", "musik favorit ponyo", "lagu favorit ponyo"]):
            return f"Ponyo suka musik 8-bit retro dan J-Pop yang ceria, bikin pengin joget {name}!"
        if any(phrase in msg for phrase in ["impian ponyo apa", "cita cita ponyo", "cita-cita ponyo", "ponyo ingin jadi apa"]):
            return f"Impian Ponyo mencapai satu juta subscriber dan mencicipi semua rasa boba di dunia, {name}!"
        if any(phrase in msg for phrase in ["ponyo umur berapa", "usia ponyo", "ponyo usianya berapa"]):
            return f"Ponyo hantu kecil dengan penampilan kira-kira seperti anak umur sepuluh tahun, {name}!"
        return ""

    def generate_reply(self, author_name: str, message: str) -> str:
        """Membuat respons chat dengan persona dan dua lapis moderasi sebelum model."""
        raw_message = message or ""
        author_name = safe_name(author_name)
        msg_clean = normalize_chat_message(raw_message.strip())
        persona_result = self.persona_moderator.check_input(author_name, msg_clean)
        if not persona_result.allowed:
            # Spam/judi dikembalikan kosong agar tidak ikut dibacakan TTS.
            blocked_reply = persona_result.reply or ""
            if persona_result.notify_host:
                print(f"[PERHATIAN HOST] Pesan serius dari {author_name} ({persona_result.category}).")
            if blocked_reply:
                blocked_reply = self.persona_moderator.check_output(blocked_reply)
            self.memory.record_chat(author_name, msg_clean)
            if blocked_reply:
                self.memory.record_reply(author_name, msg_clean, blocked_reply)
            print(f"[PERSONA FILTER] Pesan ditolak: {persona_result.category}")
            return blocked_reply
        intent = classify_chat_intent(msg_clean)
        allowed, moderation_reason = self.moderate_message(msg_clean)
        if not allowed:
            safe_reply = f"Maaf {author_name}, Ponyo tidak bisa membantu permintaan itu. Yuk ngobrol soal stream saja!"
            self.memory.record_chat(author_name, msg_clean)
            self.memory.record_reply(author_name, msg_clean, safe_reply)
            print(f"[MODERATION] Pesan ditolak: {moderation_reason}")
            return safe_reply

        # Jangan menebak istilah pendek yang belum terkonfirmasi.
        if is_unrecognized_short_term(msg_clean, slang_learner.lexicon):
            clarification = self.fallback_engine.generate(
                author_name or "teman",
                msg_clean,
                recent=list(self.recent_replies),
                intent="confused_slang",
            )
            self.memory.record_chat(author_name, msg_clean)
            self.memory.record_reply(author_name, msg_clean, clarification)
            return clarification

        # Pertanyaan fakta karakter dijawab tanpa LLM supaya tetap instan saat Ollama
        # sedang cold-start, sibuk menjalankan VLM, atau mengalami timeout.
        quick_reply = self._quick_profile_reply(author_name, msg_clean)
        if not quick_reply:
            quick_reply = self._quick_chat_reply(author_name, msg_clean)
        if quick_reply:
            self.memory.record_chat(author_name, msg_clean)
            self.memory.record_reply(author_name, msg_clean, quick_reply)
            return quick_reply

        # 1. Catat ke sistem memori sementara (RAM), pelajari slang, & update Level/Rank Penonton Setia (Nomor 6)
        self.memory.record_chat(author_name, msg_clean)
        slang_learner.track_and_learn(msg_clean)
        bonus_xp = 15 if msg_clean.startswith("!") else 0
        leveled_up, new_lvl, rank_title = viewer_loyalty.record_interaction(author_name, msg_clean, bonus_xp=bonus_xp)
        if leveled_up:
            sfx_player.play("fanfare")

        # Respon instan untuk perintah interaktif Penonton (Nomor 4 & Nomor 6 & Slither.io)
        if msg_clean.startswith("!"):
            cmd = msg_clean.lower()
            reply = ""
            if any(k in cmd for k in ["!level", "!rank", "!status", "!gelar"]):
                reply = viewer_loyalty.get_status_reply(author_name)
            elif any(k in cmd for k in ["!kuis", "!tebak", "!quiz", "!tebaktebakan"]):
                if chat_quiz.is_active():
                    reply = f"Kuis masih berlangsung nih {author_name}! Pertanyaannya: {chat_quiz.active_quiz['question']} Ayo tebak atau ketik !hint buat petunjuk!"
                else:
                    reply = chat_quiz.start_new_quiz(author_name)
            elif any(k in cmd for k in ["!hint", "!petunjuk", "!bocoran"]):
                reply = chat_quiz.get_hint()
            elif any(k in cmd for k in ["!nyerah", "!skip", "!lewat"]):
                reply = chat_quiz.forfeit()
            elif any(k in cmd for k in ["!topi", "!aksesoris", "!pakai", "!wardrobe", "!kostum"]):
                if any(w in cmd for w in ["lepas", "copot", "buka", "off", "none"]):
                    reply = f"Siap {author_name}, Ponyo sudah melepas aksesoris kepala ya!"
                elif any(w in cmd for w in ["witch", "penyihir", "sihir"]):
                    reply = f"Topi penyihir hantu terpasang atas permintaan {author_name}! Abrakadabra, Ponyo jadi penyihir imut!"
                elif any(w in cmd for w in ["ribbon", "pita", "pink"]):
                    reply = f"Pita merah muda cantik sudah terpasang rapi di kepala Ponyo berkat {author_name}!"
                elif any(w in cmd for w in ["crown", "mahkota", "raja", "queen"]):
                    reply = f"Mahkota emas kerajaan terpasang atas perintah {author_name}! Hidup Ratu Ponyo!"
                elif any(w in cmd for w in ["glasses", "kacamata", "sunglasses", "hitam"]):
                    reply = f"Kacamata hitam keren terpasang atas permintaan {author_name}! Deal with it, Ponyo keren banget kan?"
                elif any(w in cmd for w in ["flower", "bunga", "melati"]):
                    reply = f"Bunga melati harum terpasang di samping kepala Ponyo berkat {author_name}! Anggun banget!"
                elif any(w in cmd for w in ["halo", "malaikat", "angel"]):
                    reply = f"Halo malaikat kuning sudah terpasang di atas kepala Ponyo atas permintaan {author_name}!"
                elif any(w in cmd for w in ["tanduk", "setan", "iblis", "devil"]):
                    reply = f"Tanduk setan merah sudah terpasang atas permintaan {author_name}! Ponyo jadi kecil-kecil sangar!"
                elif any(w in cmd for w in ["knight", "helm", "helmet", "ksatria", "slasher", "armor"]):
                    reply = f"Keren banget! Helm ksatria Dungeon Slasher terpasang di kepala Ponyo berkat {author_name}! Saatnya Ponyo menebas monster dungeon!"
                else:
                    reply = f"Koleksi lemari Ponyo: pita, topi penyihir, mahkota emas, kacamata hitam, bunga melati, halo malaikat kuning, tanduk setan merah, dan helm ksatria! Ketik '!topi <nama>' atau tekan [H] buat coba ya, {author_name}!"
            elif any(k in cmd for k in ["!lepas", "!copot"]):
                reply = f"Siap {author_name}, aksesoris kepala Ponyo sudah dilepas!"
            elif any(k in cmd for k in ["!speed", "!kecepatan", "!tempo"]):
                found_v = None
                for part in cmd.split():
                    p_clean = part.replace(",", ".").strip("!xX")
                    try:
                        v = float(p_clean)
                        if v in [0.0, 0.5, 1.0, 1.5, 2.0] or 0.0 <= v <= 2.5:
                            found_v = v
                            break
                    except ValueError:
                        continue
                if found_v is not None:
                    if found_v == 0.0:
                        reply = f"Mode hening aktif atas permintaan {author_name}! Ponyo sekarang berbicara tanpa suara ya!"
                    else:
                        reply = f"Siap {author_name}! Kecepatan suara Ponyo diubah ke {found_v}x!"
                else:
                    reply = f"Pilihan kecepatan suara Ponyo: 0.0x (hening), 0.5x (lambat), 1.0x (normal), 1.5x (cepat), dan 2.0x (sangat cepat)! Ketik '!speed <angka>' ya, {author_name}!"
            elif any(k in cmd for k in ["!tts", "!engine"]):
                if any(w in cmd for w in ["local", "lokal", "offline", "piper"]):
                    reply = f"Siap {author_name}, mode Text to Speech lokal 100% offline via Piper diaktifkan!"
                elif any(w in cmd for w in ["cloud", "edge", "online"]):
                    reply = f"Siap {author_name}, mode suara Cloud Edge-TTS diaktifkan!"
                else:
                    reply = f"Pilihan mesin suara Ponyo: lokal (100% offline via Piper) atau cloud (Edge-TTS). Ketik '!tts lokal' atau tekan [L] ya, {author_name}!"
            elif any(k in cmd for k in ["!maaf", "!sorry", "!ampun", "!khilaf", "!ojigi"]):
                reply = f"Aduh maaf ya {author_name}! Ponyo minta maaf sebesar-besarnya atas kesalahan Ponyo tadi, jangan marah ya!"
            elif any(k in cmd for k in ["!pat", "!elus", "!headpat", "!sayang"]):
                reply = f"Hehe makasih {author_name} sudah elus-elus kepala Ponyo! Ponyo jadi senang banget!"
            elif any(k in cmd for k in ["!permen", "!kasihmakan", "!treat", "!makan"]):
                reply = f"Nyam nyam! Makasih permen manisnya {author_name}, rasanya enak banget!"
            elif any(k in cmd for k in ["!cry", "!nangis"]):
                reply = f"Hiks hiks sedih banget {author_name}... Ponyo nangis nih hiks!"
            elif any(k in cmd for k in ["!smug", "!ez"]):
                reply = f"Hehe kan Ponyo bilang juga apa {author_name}, santai aja Ponyo emang jago banget dong!"
            elif any(k in cmd for k in ["!shy", "!salting", "!blush"]):
                reply = f"Ih {author_name} bisa aja, manis banget deh bikin Ponyo jadi malu dan tersipu nih!"
            elif any(k in cmd for k in ["!hore", "!dance", "!joget"]):
                reply = f"Yaaay asik banget! Ponyo loncat dan joget hore bareng {author_name}!"
            elif any(k in cmd for k in ["!panik", "!kaget", "!shiver", "!takut"]):
                reply = f"Waduh panik banget {author_name}! Jantung hantu Ponyo deg-degan sampai menggigil nih!"
            elif any(k in cmd for k in ["!boba", "!kopi", "!minum", "!teh", "!ngopi"]):
                reply = f"Slurp slurp, nyam nyam! Makasih traktiran boba manisnya ya {author_name}, seger banget!"
            elif any(k in cmd for k in ["!ngambek", "!kesal", "!rage"]):
                reply = f"Hmph! Ponyo lagi ngambek nih sama {author_name}, kepala Ponyo sampai keluar asap uap panas!"
            elif any(k in cmd for k in ["!tomat", "!lempar", "!sandal"]):
                reply = f"Waduh ada yang lempar tomat dari {author_name}! Untung hantu Ponyo refleksnya lincah banget!"
            elif any(k in cmd for k in ["!bangun", "!wake"]):
                reply = f"Hoaam... Ponyo udah melek dan bangun lagi nih {author_name}! Ayo lanjut seru-seruan!"
            elif any(k in cmd for k in ["!turu", "!sleepy", "!ngantuk", "!tidur"]):
                reply = f"Hoaam... ngantuk banget {author_name}, waktunya Ponyo turu dan istirahat dulu ya!"
            elif any(k in cmd for k in ["!angry", "!marah"]):
                reply = f"Awas ya {author_name}! Jangan bikin Ponyo marah, nanti Ponyo balas dendam lho!"
            elif any(k in cmd for k in ["!star", "!kilau", "!glint"]):
                reply = f"Wahhh berkilau banget {author_name}! Banyak makanan gratis dan rejeki nomplok buat Ponyo!"
            elif any(k in cmd for k in ["!spin", "!putarbadan"]):
                reply = f"Waaah Ponyo berputar-putar karena {author_name}! Hehe pusing tapi seru banget!"
            elif any(k in cmd for k in ["!boost", "!ngebut", "!turbo", "!cepat", "!lari", "!speed"]):
                reply = f"Siap {author_name}, mode turbo diaktifkan! Wuuush, kita ngebut!"
            elif any(k in cmd for k in ["!putar", "!coil", "!panik", "!lingkar"]):
                reply = f"Perintah darurat dari {author_name}! Jurus melingkar bertahan diaktifkan!"
            elif any(k in cmd for k in ["!kiri", "!left"]):
                reply = f"Banting setir ke kiri atas perintah {author_name}!"
            elif any(k in cmd for k in ["!kanan", "!right"]):
                reply = f"Banting setir ke kanan atas perintah {author_name}!"
            if reply:
                self.memory.record_reply(author_name, msg_clean, reply)
                return reply

        # Cek apakah pesan penonton menjawab kuis tebak-tebakan yang sedang aktif (Saran Nomor 4)
        quiz_res = chat_quiz.check_answer(author_name, msg_clean)
        if quiz_res:
            viewer_loyalty.record_interaction(author_name, msg_clean, bonus_xp=50)
            sfx_player.play("fanfare")
            reply = quiz_res["reply"]
            self.memory.record_reply(author_name, msg_clean, reply)
            return reply

        # Jangan biarkan request chat berebut inference gate dengan warmup startup.
        # Jika warmup belum selesai dalam budget request, gunakan fallback lokal.
        if self.warmup_started and not self.warmup_done.wait(timeout=OLLAMA_REQUEST_TIMEOUT):
            fallback = sanitize_output(self._fallback_reply(author_name, msg_clean, intent=intent))
            self.recent_replies.append(fallback)
            self.memory.record_reply(author_name, msg_clean, fallback)
            return fallback

        # 2. Ambil konteks ringan; konteks mahal hanya ditambahkan saat relevan.
        mem_context = self.memory.get_memory_context_prompt(author_name)
        loyalty_context = viewer_loyalty.get_viewer_context(author_name)
        slang_context = slang_learner.get_slang_context_prompt(msg_clean)
        previous_diary = stream_reflector.get_latest_diary_context()

        # Satu prompt persona ringkas menghindari duplikasi persona lama dan baru.
        system_content = build_compact_chat_prompt("Kakak")
        if loyalty_context:
            system_content += f"\n\n{loyalty_context}"
        if slang_context:
            system_content += f"\n\n{slang_context}"
        if previous_diary:
            system_content += f"\n\n{previous_diary}"
        if mem_context:
            system_content += f"\n\n{mem_context}"

        # Konteks VLM hanya dikirim jika chat memang merujuk layar/game.
        visual_terms = ("layar", "game", "main", "nonton", "yang tampil", "itu apa", "lihat")
        needs_visual_context = any(term in msg_clean.lower() for term in visual_terms)
        vlm_desc = local_vlm.get_visual_context(trigger_refresh=False) if needs_visual_context else ""
        if vlm_desc:
            system_content += f"\n\n[Pemandangan layar saat ini]: {vlm_desc[:180]}"

        # Tambahkan pengetahuan khusus hanya saat topik Dungeon Slasher relevan,
        # agar konteks chat umum tetap ringan dan cepat.
        dungeon_topic = is_dungeon_slasher_title(message) or any(
            term in message.lower() for term in ["artifact", "relic", "roguelike", "mid-boss", "boss rush", "synergy"]
        )
        if dungeon_topic or is_dungeon_slasher_title(vlm_desc):
            system_content += f"\n\n{get_dungeon_slasher_context()}"

        user_content = f"Komentar dari {author_name}: \"{message}\""

        # 3. Eksekusi via AI Lokal Ollama dengan fallback model Qwen eksplisit.
        # Qwen cepat dipakai hanya jika model utama gagal; tidak ada pemilihan acak.
        if self.is_ready:
            candidates = self._candidate_chat_models()
            for model_name in candidates:
                try:
                    sys_prompt = system_content
                    if model_name != self.ollama_model:
                        sys_prompt += "\nGunakan jawaban singkat, ringan, dan langsung karena ini mode cadangan cepat."
                    messages = [{"role": "system", "content": sys_prompt}]
                    # Few-shot dipilih sesuai intent, maksimal tiga contoh.
                    for shot_user, shot_assistant in select_few_shot(msg_clean):
                        messages.append({"role": "user", "content": shot_user})
                        messages.append({"role": "assistant", "content": shot_assistant})
                    messages.append({"role": "user", "content": user_content})
                    payload = {
                        "model": model_name,
                        "messages": messages,
                        "stream": False,
                        "keep_alive": "5m" if model_name != self.ollama_model else "24h",
                        "options": {
                            "temperature": 0.62 if model_name == self.ollama_model else 0.72,
                            "repeat_penalty": 1.2,
                            "num_ctx": 1024,
                            "num_predict": 100,
                        }
                    }
                    resp = ollama_runtime.post_json(
                        model_name, "/api/chat", payload, timeout=OLLAMA_REQUEST_TIMEOUT
                    )
                    if resp.status_code == 200:
                        raw_reply = resp.json().get("message", {}).get("content", "")
                        cleaned = ensure_complete_sentence(self._clean_text_for_tts(raw_reply)[:260])
                        if cleaned and not is_awkward_reply(cleaned, source_message=msg_clean, intent=intent) and not self._is_repetitive(cleaned):
                            self.recent_replies.append(cleaned)
                            self.memory.record_reply(author_name, msg_clean, cleaned)
                            return cleaned
                except Exception as e:
                    print(f"[AI] Model {model_name} gagal, mencoba cadangan eksplisit: {type(e).__name__}")

        # 4. Fallback respons lokal variatif jika Ollama sedang offline/sibuk/looping
        fallback = sanitize_output(self._fallback_reply(author_name, msg_clean, intent=intent))
        self.recent_replies.append(fallback)
        self.memory.record_reply(author_name, msg_clean, fallback)
        return fallback

    def reset_memory(self):
        """Mereset total seluruh memori sementara (RAM)"""
        self.memory.clear()
        self.recent_replies.clear()

    def _fallback_reply(self, author: str, message: str, intent: str = None) -> str:
        """Fallback lokal berbasis konteks, intent, dan rotasi anti-pengulangan."""
        active_game = getattr(self.memory, "active_game", "umum") or "umum"
        return self.fallback_engine.generate(
            author or "teman",
            message,
            recent=list(self.recent_replies),
            game=active_game,
            intent=intent,
        )
