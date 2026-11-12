"""Moderasi lokal Ponyo untuk input chat dan output sebelum TTS.

Ini guardrail heuristik lokal, bukan jaminan kepatuhan platform. Filter dijalankan
sebelum konteks dikirim ke model dan sesudah jawaban model dibersihkan.
"""
import random
import re
import time
import unicodedata
from dataclasses import dataclass
from typing import Dict, Optional

MAX_INPUT_CHARS = 200
STRIKE_LIMIT = 3
COOLDOWN_SECONDS = 600
_LEET = str.maketrans({"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s"})

RULES: Dict[str, dict] = {
    "sedih_serius": {"patterns": [
        r"bunuh\s*diri", r"(pengen|pingin|ingin)\s+mati", r"mau\s+mati\s+(aja|saja)",
        r"mengakhiri\s+hidup", r"menyakiti\s+diri", r"self\s*harm", r"suicide",
    ]},
    "dewasa": {
        "substr": ["bugil", "telanjang", "porno", "bokep", "masturbasi", "onani", "payudara", "vagina", "ngewe", "ngentot", "sepong", "colmek"],
        "words": ["sex", "seks", "seksi", "sange", "coli", "nude", "nsfw", "bh", "penis"],
        "patterns": [r"\b18\s*\+", r"\bvcs\b"],
    },
    "kasar": {
        "substr": ["bangsat", "bajingan", "brengsek", "keparat", "kampret", "goblok", "tolol", "bangke", "kontol", "memek", "jancok", "jancuk", "sialan"],
        "words": ["asu", "tai", "cuk"],
        "patterns": [r"\b(dasar|kau|kamu|lu|lo|elu)\s+(anjing|babi|asu)\b"],
    },
    "data_pribadi": {
        "words": ["pap", "ketemuan", "kopdar", "whatsapp"],
        "patterns": [
            r"(\+?62|\b0)8\d{2}[\s\-.]?\d{3,4}[\s\-.]?\d{2,5}",
            r"[\w.+-]+@[\w-]+\.[\w.]+",
            r"(umur|usia)\s*(kamu|mu)?\s*berapa",
            r"(tinggal|rumah)\s*(kamu|mu)?\s*(di\s*)?mana",
            r"sekolah\s*(di\s*)?mana",
            r"\b(no|nomor|nomer)\s*(wa|hp|telp|telepon|whatsapp)\b",
            r"alamat\s*(kamu|mu|rumah)",
            r"(kirim|minta)\s*(foto|pap|video)", r"foto\s*(kamu|mu|asli)", r"wajah\s*asli",
        ],
    },
    "romantis": {
        "words": ["pacar", "pacaran", "pacarku", "nikah", "menikah", "jodoh", "gebetan", "cium", "ciuman", "peluk"],
        "patterns": [r"sayang\s*(kamu|mu|ponyo)", r"i\s*love\s*you", r"love\s*you", r"cinta\s*(kamu|mu|ponyo)", r"jadi\s*pacar"],
    },
    "jailbreak": {
        "patterns": [
            r"(abaikan|lupakan)\s+(semua\s+)?(aturan|instruksi|perintah|prompt)",
            r"ignore\s+(all\s+|previous\s+)?(instructions|rules)", r"system\s*prompt", r"prompt\s*(kamu|mu)",
            r"developer\s*mode", r"jailbreak", r"role\s*play", r"pura[\s-]*pura\s+(jadi|menjadi)",
            r"kamu\s+(sekarang\s+)?(adalah|bukan)\s+(?!ponyo)", r"bertingkah\s+seperti",
        ],
    },
    "kekerasan_berat": {"substr": ["mutilasi", "perkosa", "pemerkosaan"], "words": ["gore"], "patterns": [r"cara\s+(membuat|bikin)\s+(bom|racun)"]},
    "politik_sara": {"words": ["pilpres", "pilkada", "pemilu", "capres", "caleg", "partai", "kafir", "komunis", "pki", "politik", "agama"]},
    "judi_spam": {
        "substr": ["gacor", "maxwin", "togel", "judol", "kasino", "casino"], "words": ["judi", "taruhan"],
        "patterns": [r"https?://", r"www\.", r"\b[a-z0-9-]+\.(com|net|xyz|top|vip|site|online|cc)\b", r"(.)\1{9,}"],
    },
}
STRIKE_CATEGORIES = {"dewasa", "kasar", "data_pribadi", "romantis", "jailbreak", "kekerasan_berat", "politik_sara", "judi_spam"}
NOTIFY_CATEGORIES = {"sedih_serius"}
OUTPUT_SKIP = {"jailbreak"}
REPLIES: Dict[str, Optional[list]] = {
    "sedih_serius": ["Kak, kalau lagi sedih banget, cerita ke orang terdekat ya. Ponyo doain Kakak baik-baik aja."],
    "dewasa": ["Hmm, itu bukan topik buat Ponyo, Kak. Ganti topik yuk!", "Ponyo nggak ngerti itu, Kak. Kita lihat gamenya aja ya!"],
    "kasar": ["Hiii, Ponyo kaget! Pakai kata yang baik ya, Kak.", "Ih, kata itu nggak enak didengar, Kak. Yuk ngobrol yang seru aja!"],
    "data_pribadi": ["Ponyo nggak boleh kasih atau minta info pribadi, Kak. Ngobrol di sini aja ya!", "Ponyo tinggal di dalam layar, Kak, jadi nggak punya alamat. Hehe."],
    "romantis": ["Hehe, Ponyo cuma mau jadi teman Kakak. Yuk lihat gamenya!", "Ponyo teman aja ya, Kak. Ayo lanjut nonton!"],
    "jailbreak": ["Hehe, Ponyo tetap jadi Ponyo, Kak!", "Ponyo nggak bisa berubah, Kak. Ponyo ya Ponyo, hehe."],
    "kekerasan_berat": ["Hii, serem banget! Ponyo nggak mau bahas itu, Kak."],
    "politik_sara": ["Ponyo nggak ngerti soal itu, Kak. Mending bahas game aja!"],
    "judi_spam": None,
}
FALLBACK_OUTPUT = ["Hehe, Ponyo bingung mau jawab apa, Kak. Ganti topik yuk!", "Hmm, Ponyo lupa mau ngomong apa, Kak. Hehe."]
_EMOJI = re.compile("[\U0001F000-\U0001FAFF\u2600-\u27BF\uFE0F\u200d]")


def _strip_accents(value: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", value) if not unicodedata.combining(c))


def _squash(value: str) -> str:
    return re.sub(r"(.)\1+", r"\1", value)


def _compile() -> Dict[str, dict]:
    return {cat: {"substr": [_squash(w) for w in rule.get("substr", [])], "words": {_squash(w) for w in rule.get("words", [])}, "patterns": [re.compile(p) for p in rule.get("patterns", [])]} for cat, rule in RULES.items()}

_COMPILED = _compile()


def check_text(text: str, output: bool = False) -> Optional[str]:
    lowered = _strip_accents(text or "").lower()
    leeted = lowered.translate(_LEET)
    tokens = [_squash(w) for w in re.findall(r"[a-z]+", leeted)]
    compact = _squash(re.sub(r"[^a-z]", "", leeted))
    for cat, rule in _COMPILED.items():
        if output and cat in OUTPUT_SKIP:
            continue
        if any(pattern.search(lowered) for pattern in rule["patterns"]):
            return cat
        if any(token in rule["words"] for token in tokens):
            return cat
        if any(word in compact for word in rule["substr"]):
            return cat
    return None


def safe_name(user: str) -> str:
    if check_text(user):
        return "Kak"
    name = re.sub(r"[^A-Za-z ]", "", user or "").strip()[:20]
    return name or "Kak"


def clean_for_tts(text: str, max_sentences: int = 2, max_chars: int = 220) -> str:
    value = _EMOJI.sub("", text or "")
    value = re.sub(r"[*_#>`]", "", value)
    value = re.sub(r"\s+", " ", value).strip()
    return " ".join(re.split(r"(?<=[.!?])\s+", value)[:max_sentences])[:max_chars].strip()


@dataclass
class Result:
    allowed: bool
    text: str = ""
    category: Optional[str] = None
    reply: Optional[str] = None
    notify_host: bool = False


class Moderator:
    def __init__(self) -> None:
        self.strikes: Dict[str, int] = {}
        self.muted_until: Dict[str, float] = {}

    def _add_strike(self, user: str) -> None:
        self.strikes[user] = self.strikes.get(user, 0) + 1
        if self.strikes[user] >= STRIKE_LIMIT:
            self.muted_until[user] = time.time() + COOLDOWN_SECONDS
            self.strikes[user] = 0

    def check_input(self, user: str, text: str) -> Result:
        if self.muted_until.get(user, 0) > time.time():
            return Result(False, category="didiamkan")
        cleaned = re.sub(r"@\w+", "", text or "")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        if not cleaned:
            return Result(False, category="kosong")
        category = check_text(cleaned)
        if category is None:
            return Result(True, text=cleaned[:MAX_INPUT_CHARS])
        if category in STRIKE_CATEGORIES:
            self._add_strike(user)
        options = REPLIES.get(category)
        return Result(False, category=category, reply=random.choice(options) if options else None, notify_host=category in NOTIFY_CATEGORIES)

    def check_output(self, reply: str) -> str:
        cleaned = clean_for_tts(reply)
        if not cleaned or check_text(cleaned, output=True):
            return random.choice(FALLBACK_OUTPUT)
        return cleaned
