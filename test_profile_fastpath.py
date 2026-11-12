from ai_brain import AIBrain


def test_food_profile_question_uses_instant_reply():
    reply = AIBrain._quick_profile_reply("Viewer", "ponyo makanan kesukaannya apa?")
    assert reply
    assert "permen lollipop" in reply.lower()
    assert "mochi" in reply.lower()
    assert "aku" not in reply.lower()
    assert "saya" not in reply.lower()


def test_non_profile_question_returns_empty_fastpath():
    assert AIBrain._quick_profile_reply("Viewer", "lagi main apa?") == ""


def test_light_chat_uses_local_fastpath():
    assert "Ponyo" in AIBrain._quick_chat_reply("Viewer", "hai Ponyo")
    assert "makasih" in AIBrain._quick_chat_reply("Viewer", "makasih Ponyo").lower()
    assert "semangat" in AIBrain._quick_chat_reply("Viewer", "semangat Ponyo").lower()
    assert AIBrain._quick_chat_reply("Viewer", "jelaskan strategi game ini") == ""


if __name__ == "__main__":
    test_food_profile_question_uses_instant_reply()
    test_non_profile_question_returns_empty_fastpath()
    test_light_chat_uses_local_fastpath()
    print("Profile fast-path tests passed")
