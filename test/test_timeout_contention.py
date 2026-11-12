"""Regression tests for chat priority under Ollama contention."""
import threading
import time

from ponyo.ollama_runtime import OllamaRuntime


def test_low_priority_lane_fails_fast_when_inference_is_busy():
    runtime = OllamaRuntime(url="http://127.0.0.1:1", timeout=0.5, max_attempts=1)
    started = threading.Event()
    release = threading.Event()

    def hold_gate():
        runtime.inference_gate.acquire()
        started.set()
        release.wait(0.4)
        runtime.inference_gate.release()

    holder = threading.Thread(target=hold_gate, daemon=True)
    holder.start()
    assert started.wait(1)
    began = time.monotonic()
    try:
        runtime.post_json(
            "moondream:latest", "/api/generate", {},
            timeout=0.5, gate_timeout=0.05, lane="vlm"
        )
    except TimeoutError:
        pass
    elapsed = time.monotonic() - began
    release.set()
    holder.join(1)
    assert elapsed < 0.25, elapsed


def test_runtime_accepts_chat_lane_and_keeps_gate_timeout_bounded():
    runtime = OllamaRuntime(url="http://127.0.0.1:1", timeout=0.2, max_attempts=1)
    assert runtime._gate_timeout("chat", None) == 0.2
    assert runtime._gate_timeout("yapping", 0.05) == 0.05


if __name__ == "__main__":
    test_low_priority_lane_fails_fast_when_inference_is_busy()
    test_runtime_accepts_chat_lane_and_keeps_gate_timeout_bounded()
    print("Timeout contention tests passed")
