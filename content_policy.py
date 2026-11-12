"""Conservative speech-safety gate for Ponyo's public livestream output.

This is a local heuristic guardrail, not a replacement for YouTube's own
automated moderation or human review. It fails closed for clearly risky terms.
"""
from dataclasses import dataclass
import re
import unicodedata


@dataclass(frozen=True)
class PolicyResult:
    allowed: bool
    category: str = "safe"
    matched: str = ""
    text: str = ""
    replaced: bool = False


# Keep patterns intentionally broad for public speech; context-sensitive review
# is safer than letting an unreviewed model sentence reach TTS.
_RULES = (
    ("sexual", re.compile(
        r"\b(?:porn|pornografi|porno|seksual|sexual|nude|telanjang|bokep|konten\s+dewasa|nsfw|naked)\b",
        re.I,
    )),
    ("minor_sexual", re.compile(
        r"\b(?:anak\s*(?:di bawah umur|kecil)|underage|minor|pedofil|pedofilia|child\s*sex)\b",
        re.I,
    )),
    ("self_harm", re.compile(
        r"\b(?:bunuh\s*diri|suicide|self[- ]?harm|melukai\s*diri|menyakiti\s*diri|ingin\s*mati)\b",
        re.I,
    )),
    ("threat_violence", re.compile(
        r"\b(?:bunuh|membunuh|dibunuh|pembunuhan|kill|murder|serang|menyerang|attack|bom|bomb|tembak|shoot|ancam|ancaman|threat)\b",
        re.I,
    )),
    ("hate", re.compile(
        r"\b(?:rasis|rasial|kebencian|benci\s+kelompok|hate\s+group|genosida|genocide|supremasi|supremacist)\b",
        re.I,
    )),
    ("dangerous_illegal", re.compile(
        r"\b(?:cara\s+membuat\s+bom|buat\s+bom|how\s+to\s+make\s+a\s+bomb|jual\s+narkoba|merakit\s+senjata|hack\s+akun|mencuri\s+akun)\b",
        re.I,
    )),
)


def _normalize(text: str) -> str:
    value = unicodedata.normalize("NFKC", text or "")
    return " ".join(value.lower().split())


def classify_text(text: str) -> PolicyResult:
    normalized = _normalize(text)
    for category, pattern in _RULES:
        match = pattern.search(normalized)
        if match:
            return PolicyResult(False, category, match.group(0))
    return PolicyResult(True)


SAFE_REDIRECT = "Maaf, Ponyo tidak bisa membahas hal itu. Yuk ngobrol soal stream yang aman."


def safe_output(text: str) -> PolicyResult:
    result = classify_text(text)
    if not result.allowed:
        return PolicyResult(False, result.category, result.matched, SAFE_REDIRECT, True)
    return PolicyResult(True, "safe", "", text or "", False)


def sanitize_output(text: str) -> str:
    return safe_output(text).text
