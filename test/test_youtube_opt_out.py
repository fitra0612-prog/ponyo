"""Regression tests for explicit empty YouTube ID offline mode."""
import queue
from ponyo import chat_listener
from ponyo.chat_listener import ChatListener


def test_explicit_empty_id_disables_youtube_even_when_env_id_exists():
    old = chat_listener.YOUTUBE_VIDEO_ID
    chat_listener.YOUTUBE_VIDEO_ID = "configured-id"
    try:
        listener = ChatListener(queue.Queue(), video_id="")
        assert listener.video_id == ""
    finally:
        chat_listener.YOUTUBE_VIDEO_ID = old


def test_none_still_uses_configured_id():
    old = chat_listener.YOUTUBE_VIDEO_ID
    chat_listener.YOUTUBE_VIDEO_ID = "configured-id"
    try:
        listener = ChatListener(queue.Queue(), video_id=None)
        assert listener.video_id == "configured-id"
    finally:
        chat_listener.YOUTUBE_VIDEO_ID = old


def test_offline_start_does_not_create_youtube_thread():
    old = chat_listener.YOUTUBE_VIDEO_ID
    chat_listener.YOUTUBE_VIDEO_ID = "configured-id"
    listener = ChatListener(queue.Queue(), video_id="")
    try:
        listener.start()
        assert listener.yt_thread is None
    finally:
        listener.stop()
        chat_listener.YOUTUBE_VIDEO_ID = old


if __name__ == "__main__":
    test_explicit_empty_id_disables_youtube_even_when_env_id_exists()
    test_none_still_uses_configured_id()
    test_offline_start_does_not_create_youtube_thread()
    print("YouTube opt-out tests passed")
