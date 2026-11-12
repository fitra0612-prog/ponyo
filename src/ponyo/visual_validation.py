"""Deterministic visual evidence fusion for safe game classification."""
import re

from .yapping_catalog import classify_screen


def _tokens(text):
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def classify_visual_context(window_title: str = "", ocr_text: str = "", vlm_text: str = "") -> dict:
    """Fuse window title, OCR, and VLM evidence without inventing unseen details."""
    sources = {
        "title": window_title or "",
        "ocr": ocr_text or "",
        "vlm": vlm_text or "",
    }
    scores = {}
    evidence = {}
    for source, text in sources.items():
        category = classify_screen(text)
        if category == "CASUAL_STREAM":
            continue
        weight = {"title": 0.60, "ocr": 0.35, "vlm": 0.20}[source]
        scores[category] = scores.get(category, 0.0) + weight
        evidence.setdefault(category, []).append(source)

    if not scores:
        return {"category": classify_screen(window_title), "confidence": 0.0, "evidence": [], "conflict": False}

    ranked = sorted(scores.items(), key=lambda item: item[1], reverse=True)
    category, score = ranked[0]
    second_score = ranked[1][1] if len(ranked) > 1 else 0.0
    conflict = len(ranked) > 1 and second_score >= 0.25 and (score - second_score) <= 0.50
    confidence = min(1.0, score + (0.10 if len(evidence.get(category, [])) > 1 else 0.0))
    if "ocr" in evidence.get(category, []) and category != "CASUAL_STREAM":
        confidence = max(confidence, 0.55)
    return {
        "category": category,
        "confidence": round(confidence, 3),
        "evidence": evidence.get(category, []),
        "conflict": conflict,
        "alternatives": [item[0] for item in ranked[1:]],
    }
