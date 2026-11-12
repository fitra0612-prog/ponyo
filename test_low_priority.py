"""Regression tests for low-priority resilience and personalization improvements."""
import json

from ai_brain import AIBrain
from config import QWEN_FAST_MODEL, QWEN_FALLBACK_MODEL
from fallback_engine import FallbackResponseEngine
from session_memory import SessionMemory
from visual_validation import classify_visual_context


def test_qwen_models_are_explicit_and_selected_only_when_available():
    brain = AIBrain.__new__(AIBrain)
    brain.ollama_model = "qwen2.5:3b"
    brain.available_models = {"qwen2.5:3b", "moondream:latest"}
    assert brain._candidate_chat_models() == ["qwen2.5:3b"]

    brain.available_models = {"moondream:latest"}
    assert brain._candidate_chat_models() == []


def test_visual_validation_combines_title_ocr_and_vlm():
    result = classify_visual_context(
        "Browser - New Tab",
        "Dungeon Slasher boss arena artifact",
        "Terlihat karakter game dan monster di arena",
    )
    assert result["category"] == "GAME_DUNGEON_SLASHER"
    assert result["confidence"] >= 0.5
    assert "ocr" in result["evidence"]

    conflict = classify_visual_context("Chess.com", "Dungeon Slasher", "papan catur")
    assert conflict["conflict"] is True


def test_session_viewer_memory_has_structured_profile_and_topics():
    memory = SessionMemory()
    memory.record_chat("Rina", "Namaku Rina, aku dari Bandung dan suka main gitar")
    memory.record_chat("Rina", "Ponyo, game ini seru banget")
    profile = memory.get_viewer_profile("Rina")
    assert profile["display_name"] == "Rina"
    assert profile["profile"]["name"] == "Rina"
    assert profile["profile"]["location"] == "Bandung"
    assert "main gitar" in profile["profile"]["interests"]
    assert profile["topics"]["game"] >= 1
    assert "Bandung" in memory.get_memory_context_prompt("Rina")


def test_fallback_engine_varies_without_forbidden_self_pronouns():
    engine = FallbackResponseEngine()
    recent = []
    outputs = [engine.generate("Rina", "hai Ponyo", recent, game="Slither.io") for _ in range(5)]
    assert len(set(outputs)) >= 3
    joined = " ".join(outputs).lower()
    assert " aku " not in f" {joined} "
    assert " saya " not in f" {joined} "
    assert all("*" not in output for output in outputs)


if __name__ == "__main__":
    test_qwen_models_are_explicit_and_selected_only_when_available()
    test_visual_validation_combines_title_ocr_and_vlm()
    test_session_viewer_memory_has_structured_profile_and_topics()
    test_fallback_engine_varies_without_forbidden_self_pronouns()
    print("Low priority tests passed")
