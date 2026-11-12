"""Focused tests for integrating Ponyo persona and chat moderation."""
from ponyo_filter import Moderator, check_text, clean_for_tts
from ponyo_persona import build_persona_prompt, build_messages


def test_filter_blocks_sensitive_input_and_returns_character_reply():
    mod = Moderator()
    result = mod.check_input("Rina", "jadi pacar Ponyo ya")
    assert not result.allowed
    assert result.category == "romantis"
    assert result.reply
    assert "Ponyo" in result.reply


def test_filter_preserves_safe_game_language():
    mod = Moderator()
    result = mod.check_input("Budi", "bunuh musuhnya di game lalu mabar")
    assert result.allowed
    assert result.text


def test_filter_mutes_repeated_abuse():
    mod = Moderator()
    for _ in range(3):
        result = mod.check_input("Troll", "k0nt0l lu")
        assert not result.allowed
    muted = mod.check_input("Troll", "halo Ponyo")
    assert not muted.allowed
    assert muted.category == "didiamkan"


def test_output_filter_removes_format_and_rejects_unsafe_text():
    mod = Moderator()
    assert clean_for_tts("**Hiii Kak!**") == "Hiii Kak!"
    safe = mod.check_output("Ponyo senang, Kak!")
    assert safe == "Ponyo senang, Kak!"
    unsafe = mod.check_output("Ponyo mau bahas bokep")
    assert unsafe != "Ponyo mau bahas bokep"
    assert "Ponyo" in unsafe


def test_persona_prompt_is_safe_and_third_person():
    prompt = build_persona_prompt("Kakak")
    lowered = prompt.lower()
    assert "sebut dirimu ponyo" in lowered
    assert "tanpa emoji" in lowered
    assert "bukan manusia atau anak nyata" in lowered
    assert "maksimal 2 kalimat" in lowered
    assert "kak" in lowered


def test_persona_messages_include_few_shot_and_latest_message():
    messages = build_messages("Kakak", "Rina: Hai Ponyo!")
    assert messages[0]["role"] == "system"
    assert any("Hai Ponyo" in item["content"] for item in messages if item["role"] == "user")
    assert messages[-1] == {"role": "user", "content": "Rina: Hai Ponyo!"}


if __name__ == "__main__":
    for name, value in list(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
    print("Persona filter integration tests passed")
