"""Regression tests for natural playful auto-yapping."""
from unittest.mock import patch

from ponyo.screen_commentator import ScreenCommentator
from ponyo.yapping_catalog import get_playful_yap, PLAYFUL_YAPS


class DummyBrain:
    is_ready = False
    ollama_model = "qwen2.5:3b"


def test_playful_catalog_has_safe_childlike_lines():
    assert len(PLAYFUL_YAPS) >= 8
    for line in PLAYFUL_YAPS:
        lower = line.lower()
        assert line
        assert "aku" not in lower
        assert "saya" not in lower
        assert "gua" not in lower
        assert "gue" not in lower
        assert "stockfish" not in lower
        assert "emoji" not in lower


def test_playful_yap_does_not_require_screen_context():
    line = get_playful_yap([])
    assert line
    assert "ponyo" in line.lower()


def test_commentator_can_yap_playfully_without_screen():
    commentator = ScreenCommentator(DummyBrain(), yap_interval=25)
    with patch.object(commentator, "get_screen_context", return_value=""), \
         patch("ponyo.screen_commentator.random.random", return_value=0.0):
        result = commentator.generate_yap()
    assert result
    assert result in PLAYFUL_YAPS
    assert commentator.recent_yaps[-1] == result


def test_commentator_randomly_chooses_playful_mode_with_screen():
    commentator = ScreenCommentator(DummyBrain(), yap_interval=25)
    with patch.object(commentator, "get_screen_context", return_value="Minecraft"), \
         patch("ponyo.screen_commentator.random.random", return_value=0.0), \
         patch("ponyo.screen_commentator.screen_ocr.screen_ocr.extract_screen_text", return_value=""), \
         patch("ponyo.screen_commentator.local_vlm.local_vlm.get_visual_context", return_value=""):
        result = commentator.generate_yap()
    assert result
    assert result in PLAYFUL_YAPS


if __name__ == "__main__":
    for name, value in list(globals().items()):
        if name.startswith("test_") and callable(value):
            value()
    print("Playful yapping tests passed")
