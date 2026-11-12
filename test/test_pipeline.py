
def test_all():
    print("[TEST 1/3] Testing AI Brain...")
    from ponyo.ai_brain import AIBrain
    brain = AIBrain()
    reply = brain.generate_reply("Audience", "Halo apa kabar VTuber!")
    print(f"Reply generated: '{reply}'")
    assert len(reply) > 0, "Reply must not be empty"

    print("\n[TEST 2/3] Testing TTS Engine...")
    from ponyo.tts_engine import TTSEngine
    tts = TTSEngine()
    tts.speak_text("Halo dunia!")
    assert not tts.is_speaking, "is_speaking should be False after finishing"

    print("\n[TEST 3/3] Testing VTuber Display...")
    from ponyo.vtuber_display import VTuberDisplay
    display = VTuberDisplay(tts)
    # Run a few frames
    for _ in range(5):
        display.run_frame()
    display.close()
    print("Display OK!")

    print("\nALL PIPELINE TESTS PASSED!")

if __name__ == "__main__":
    test_all()
