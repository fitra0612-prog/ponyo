"""Lightweight Indonesian chat normalization and reply quality gates."""
import re
from typing import Mapping


_REPEAT_LETTERS = re.compile(r"([a-zA-Z])\1{2,}")
_TYPO_MAP = {
    "gaskeunn": "gaskeun",
    "gaskeun": "gaskeun",
    "mabarrr": "mabar",
    "mabarr": "mabar",
    "kuyy": "kuy",
    "donggg": "dong",
    "ponyyy": "ponyo",
}


def normalize_chat_message(message: str) -> str:
    """Normalize common livestream elongations without rewriting the raw chat."""
    text = " ".join((message or "").split())

    def replace_word(match):
        word = match.group(0)
        lowered = word.lower()
        reduced = _REPEAT_LETTERS.sub(r"\1\1", lowered)
        replacement = _TYPO_MAP.get(lowered, _TYPO_MAP.get(reduced, reduced))
        return replacement.capitalize() if word[:1].isupper() else replacement

    return re.sub(r"[A-Za-zÀ-ÿ]+", replace_word, text)


def is_unrecognized_short_term(message: str, lexicon: Mapping[str, dict]) -> bool:
    text = normalize_chat_message(message).lower().strip()
    if not re.fullmatch(r"[a-z0-9_-]{2,12}", text):
        return False
    if text in {
        "halo", "hai", "hello", "wkwk", "wkwkwk", "haha", "hehe", "lol", "kuy",
        "ponyo", "keren", "jago", "hebat", "mantap", "makasih", "terima", "kasih",
        "semangat", "game", "main", "catur", "slither", "iya", "tidak", "nggak",
        "apa", "siapa", "bantu", "topi", "hore", "pat", "boba", "turu",
    }:
        return False
    item = lexicon.get(text)
    return item is None or float(item.get("confidence", 1.0)) < 0.8


def classify_chat_intent(message: str) -> str:
    text = normalize_chat_message(message).lower().strip()
    if not text:
        return "short_message"
    if len(text.split()) <= 2:
        if any(x in text for x in ("halo", "hai", "hello", "hi")):
            return "greeting"
        if text in {"wkwk", "wkwkwk", "haha", "hehe", "lol", "xixixi"}:
            return "short_message"
    if any(x in text for x in ("maksudnya apa", "artinya apa", "itu apa", "apa itu", "belum paham")):
        return "confused_slang"
    if any(x in text for x in ("jago", "keren", "hebat", "gg", "mantap", "pro banget")):
        return "compliment"
    if any(x in text for x in ("kalah", "mati", "gagal", "blunder", "keok")):
        return "game_failure"
    if "?" in text or any(x in text for x in ("apa", "gimana", "bagaimana", "kenapa", "spill", "jelasin")):
        return "question"
    if any(x in text for x in ("gas", "gaskeun", "mabar", "semangat", "kuy")):
        return "support"
    if len(text.split()) <= 2:
        return "short_message"
    return "general"


def select_relevant_slangs(message: str, lexicon: Mapping[str, dict]) -> str:
    """Return only trusted slang entries relevant to this message."""
    normalized = normalize_chat_message(message).lower()
    words = set(re.findall(r"[a-z0-9_-]+", normalized))
    lines = []
    for key, item in lexicon.items():
        confidence = float(item.get("confidence", 1.0))
        term = str(item.get("term", key))
        if confidence < 0.8:
            continue
        if key.lower() in words or term.lower() in normalized:
            lines.append(f"- {term}: {item.get('meaning', '')}.")
    return "ISTILAH CHAT YANG RELEVAN:\n" + "\n".join(lines) if lines else ""


def is_awkward_reply(reply: str, source_message: str = "", intent: str = "") -> bool:
    """Reject formal, overlong, repetitive, or intent-mismatched public speech."""
    text = " ".join((reply or "").split())
    source = normalize_chat_message(source_message).lower() if source_message else ""
    lowered = text.lower()
    formal_markers = (
        "ponyо memahami bahwa", "ponyo memahami bahwa", "berdasarkan informasi tersebut",
        "sebagai ai", "dapat disimpulkan", "pengguna tersebut", "saya dapat membantu",
    )
    if any(marker in lowered for marker in formal_markers):
        return True
    if len(text.split()) > 42 or text.count(",") >= 5:
        return True
    if intent == "compliment" and not any(marker in lowered for marker in ("makasih", "senang", "semangat", "wah")):
        return True
    if intent == "confused_slang" and not any(marker in lowered for marker in ("belum", "paham", "arti", "jelas", "maksud")):
        return True
    if source and intent == "question" and "?" not in source and len(text.split()) > 32:
        return True
    words = re.findall(r"[a-zA-ZÀ-ÿ]+", lowered)
    if len(words) >= 8 and len(set(words)) / len(words) < 0.45:
        return True
    return False
