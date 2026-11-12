"""Focused regression tests for worker isolation, health, diary context, and logging."""
import json
import threading
import time

from ponyo.ollama_runtime import OllamaCircuitBreaker, OllamaRuntime
from ponyo.session_memory import SessionMemory
from ponyo.self_improvement import PostStreamReflector
from ponyo.structured_logging import StructuredLogger, structured_logger
from ponyo.worker_runtime import WorkerRuntime


def test_worker_runtime_has_isolated_lanes():
    workers = WorkerRuntime(start=False)
    assert set(workers.queues) == {"chat", "tts", "vlm", "yapping"}
    assert workers.submit("chat", lambda: "chat")
    assert workers.submit("tts", lambda: "tts")
    assert workers.queue_sizes()["chat"] == 1
    assert workers.queue_sizes()["tts"] == 1
    workers.stop()


def test_runtime_timeout_and_resource_conflict_are_bounded():
    breaker = OllamaCircuitBreaker(failure_threshold=5, cooldown_seconds=0.1)
    runtime = OllamaRuntime(url="http://127.0.0.1:1", timeout=0.05, max_attempts=1, breaker=breaker)
    started = threading.Event()
    release = threading.Event()

    def hold_gate():
        runtime.inference_gate.acquire()
        started.set()
        release.wait(0.5)
        runtime.inference_gate.release()

    holder = threading.Thread(target=hold_gate, daemon=True)
    holder.start()
    assert started.wait(1)
    began = time.monotonic()
    try:
        runtime.post_json("test-model", "/api/chat", {}, timeout=0.05)
    except Exception:
        pass
    assert time.monotonic() - began < 0.5
    release.set()
    holder.join(1)


def test_health_monitor_reports_state_without_secrets():
    from ponyo.ollama_runtime import OllamaHealthMonitor
    monitor = OllamaHealthMonitor(url="http://127.0.0.1:1", timeout=0.05)
    result = monitor.check()
    assert result["status"] in {"offline", "degraded", "healthy"}
    assert "password" not in json.dumps(result).lower()


def test_diary_uses_active_game_context():
    memory = SessionMemory()
    memory.set_active_game("Dungeon Slasher")
    memory.record_game_event("DEATH")
    summary = memory.get_session_summary_data()
    assert summary["active_game"] == "Dungeon Slasher"
    assert summary["game_stats"]["game"] == "Dungeon Slasher"

    reflector = PostStreamReflector(filepath="test_diary_medium.json", model="missing")
    prompt = reflector.build_reflection_prompt(summary)
    assert "Dungeon Slasher" in prompt
    try:
        import os
        os.remove("test_diary_medium.json")
    except OSError:
        pass


def test_structured_logger_emits_json():
    records = []
    logger = StructuredLogger(sink=records.append)
    logger.warning("ollama_timeout", model="moondream", timeout=8)
    data = json.loads(records[0])
    assert data["event"] == "ollama_timeout"
    assert data["model"] == "moondream"
    assert "timestamp" in data


def test_worker_task_failure_is_logged_as_structured_event():
    records = []
    original_sink = structured_logger._sink
    structured_logger._sink = records.append
    workers = WorkerRuntime(start=True)
    try:
        assert workers.submit("chat", lambda: (_ for _ in ()).throw(ValueError("boom")))
        deadline = time.time() + 1.0
        while time.time() < deadline and not records:
            time.sleep(0.01)
        assert records
        event = json.loads(records[0])
        assert event["event"] == "worker_task_failed"
        assert event["lane"] == "chat"
        assert event["error"] == "ValueError"
    finally:
        workers.stop()
        structured_logger._sink = original_sink


if __name__ == "__main__":
    test_worker_runtime_has_isolated_lanes()
    test_runtime_timeout_and_resource_conflict_are_bounded()
    test_health_monitor_reports_state_without_secrets()
    test_diary_uses_active_game_context()
    test_structured_logger_emits_json()
    print("Medium priority tests passed")
