"""Focused regression tests for natural Indonesian livestream replies."""
import tempfile
import os

from ponyo.fallback_engine import FallbackResponseEngine
from ponyo.language_naturalness import (
    classify_chat_intent,
    is_awkward_reply,
    is_unrecognized_short_term,
    normalize_chat_message,
    select_relevant_slangs,
)
from ponyo.self_improvement import DynamicVocabularyLearner
from ponyo.config import VTUBER_SYSTEM_PROMPT


def test_normalize_typo_preserves_meaning():
    raw = "Ponyo gaskeunnn, mabarrr kuy!!!"
    assert normalize_chat_message(raw) == "Ponyo gaskeun, mabar kuy!!!"


def test_slang_learning_requires_confirmation_before_usage():
    with tempfile.TemporaryDirectory() as directory:
        path = os.path.join(directory, "slang.json")
        learner = DynamicVocabularyLearner(path)
        learner.track_and_learn("ngab itu sapaan santai")
        assert learner.lexicon["ngab"]["confirmed_count"] == 1
        assert learner.lexicon["ngab"]["confidence"] < 0.8
        assert "ngab" not in learner.get_slang_context_prompt()
        learner.track_and_learn("ngab itu sapaan santai")
        assert learner.lexicon["ngab"]["confirmed_count"] == 2
        assert learner.lexicon["ngab"]["confidence"] >= 0.8
        assert "NGAB" in learner.get_slang_context_prompt("ngab")


def test_relevant_slang_context_is_filtered():
    lexicon = {
        "gas": {"term": "Gas", "meaning": "lanjut", "confidence": 1.0},
        "mabar": {"term": "Mabar", "meaning": "main bersama", "confidence": 1.0},
        "spill": {"term": "Spill", "meaning": "ceritakan", "confidence": 1.0},
    }
    result = select_relevant_slangs("ayo mabar game", lexicon)
    assert "Mabar" in result
    assert "Spill" not in result


def test_quality_gate_rejects_formal_long_and_mismatched_output():
    assert is_awkward_reply("Ponyo memahami bahwa permainan tersebut sangat menarik.")
    assert is_awkward_reply(" ".join(["Ponyo"] * 45))
    assert is_awkward_reply(
        "Hari ini Ponyo menonton live setiap hari, kabarewa dan tidak nyangkut.",
        source_message="Ponyo jago banget",
        intent="compliment",
    )
    assert not is_awkward_reply(
        "Wah makasih, Ponyo jadi makin semangat nih!",
        source_message="Ponyo jago banget",
        intent="compliment",
    )
    assert not is_awkward_reply("Wah seru banget, Ponyo ikut tegang nih!")


def test_prompt_contains_natural_language_rules():
    assert "reaksi langsung" in VTUBER_SYSTEM_PROMPT
    assert "Jangan menerjemahkan slang" in VTUBER_SYSTEM_PROMPT
    assert "pembuka kaku" in VTUBER_SYSTEM_PROMPT


def test_chat_intent_classification():
    assert classify_chat_intent("Ponyo kamu jago banget") == "compliment"
    assert classify_chat_intent("spill dong build-nya") == "question"
    assert classify_chat_intent("ngab") == "short_message"
    assert classify_chat_intent("maksudnya apa itu istilah baru") == "confused_slang"


def test_unknown_short_term_is_detected_without_guessing():
    assert is_unrecognized_short_term("ngab", {"gas": {"confidence": 1.0}})
    assert not is_unrecognized_short_term("gas", {"gas": {"confidence": 1.0}})
    assert not is_unrecognized_short_term("halo", {"gas": {"confidence": 1.0}})


def test_fallback_has_intent_specific_responses():
    engine = FallbackResponseEngine()
    reply = engine.generate("HFI", "ngab", intent="confused_slang")
    assert "paham" in reply.lower() or "artinya" in reply.lower()
    reply = engine.generate("HFI", "Ponyo jago", intent="compliment")
    assert "makasih" in reply.lower() or "senang" in reply.lower()


EVALUATION_CASES = [
    ("halo Ponyo", "greeting"),
    ("Ponyo gaskeun", "support"),
    ("Ponyo jago banget", "compliment"),
    ("spill build dong", "question"),
    ("wkwkwk", "short_message"),
    ("ngab itu apa", "confused_slang"),
    ("mabar kuy", "support"),
    ("yah kalah lagi", "game_failure"),
    ("GG Ponyo", "compliment"),
    ("kok bisa begitu", "question"),
]


def test_indonesian_evaluation_corpus_is_available():
    assert len(EVALUATION_CASES) >= 10
    assert all(message and intent for message, intent in EVALUATION_CASES)


if __name__ == "__main__":
    for name, value in list(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
    print("Indonesian naturalness tests passed")
