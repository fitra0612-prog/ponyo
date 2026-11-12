
from ponyo.runtime_metrics import RuntimeMetrics
from ponyo.worker_runtime import WorkerRuntime
from ponyo.tts_engine import TTSEngine
from ponyo.chat_listener import ChatListener


def test_runtime_metrics_percentiles_and_counters():
    metrics = RuntimeMetrics(history_size=10)
    for value in (10, 20, 30, 40, 50):
        metrics.observe("chat_latency_ms", value)
    metrics.increment("fallback_count")
    metrics.increment("fallback_count")
    snapshot = metrics.snapshot()
    assert snapshot["counters"]["fallback_count"] == 2
    assert snapshot["timings"]["chat_latency_ms"]["count"] == 5
    assert snapshot["timings"]["chat_latency_ms"]["p95"] >= 40
    assert snapshot["timings"]["chat_latency_ms"]["p99"] >= 40


def test_worker_can_drop_stale_tts_jobs():
    workers = WorkerRuntime(start=False)
    try:
        assert workers.submit("tts", lambda: None)
        assert workers.submit("tts", lambda: None)
        assert workers.clear_lane("tts") == 2
        assert workers.queue_sizes()["tts"] == 0
    finally:
        workers.stop()


def test_tts_emergency_silence_stops_future_speech():
    tts = TTSEngine.__new__(TTSEngine)
    tts.is_muted = False
    tts.emergency_silence = False
    tts.current_text = "sedang bicara"
    tts.is_speaking = True
    tts.set_emergency_silence(True)
    assert tts.emergency_silence is True
    assert tts.is_muted is True
    assert tts.current_text == ""
    assert tts.is_speaking is False
    assert tts.can_speak() is False
    tts.set_emergency_silence(False)
    assert tts.emergency_silence is False
    assert tts.is_muted is False
    assert tts.can_speak() is True

    tts.is_muted = True
    tts.set_emergency_silence(True)
    tts.set_emergency_silence(False)
    assert tts.is_muted is True
    assert tts.can_speak() is False
    tts.is_muted = False
    tts.emergency_silence = False
    assert tts.can_speak() is True


def test_youtube_retry_delay_is_bounded_exponential():
    assert ChatListener.retry_delay(0) == 1.0
    assert ChatListener.retry_delay(1) == 2.0
    assert ChatListener.retry_delay(10) == 30.0


if __name__ == "__main__":
    test_runtime_metrics_percentiles_and_counters()
    test_worker_can_drop_stale_tts_jobs()
    test_tts_emergency_silence_stops_future_speech()
    test_youtube_retry_delay_is_bounded_exponential()
    print("Production hardening tests passed")
