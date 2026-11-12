from ponyo.ai_brain import AIBrain
from ponyo.ponyo_persona import select_few_shot, build_compact_chat_prompt


def test_compact_prompt_is_smaller_than_legacy_prompt():
    compact = build_compact_chat_prompt("Kakak")
    assert len(compact) < 900
    assert "Ponyo" in compact
    assert "maksimal 2 kalimat" in compact


def test_few_shot_is_bounded_and_relevant():
    shots = select_few_shot("ini game apa Ponyo?")
    assert 1 <= len(shots) <= 3
    assert len(shots) < 7
    assert any("game" in user.lower() for user, _ in shots)


def test_warmup_event_exists_and_is_initially_pending_without_ollama():
    brain = AIBrain.__new__(AIBrain)
    brain._init_latency_state()
    assert hasattr(brain, "warmup_done")
    assert not brain.warmup_done.is_set()


if __name__ == "__main__":
    test_compact_prompt_is_smaller_than_legacy_prompt()
    test_few_shot_is_bounded_and_relevant()
    test_warmup_event_exists_and_is_initially_pending_without_ollama()
    print("Latency optimization tests passed")
