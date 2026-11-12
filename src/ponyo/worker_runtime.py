"""Isolated bounded workers for latency-sensitive stream subsystems."""
import queue
import threading
from typing import Callable

from .structured_logging import structured_logger


class WorkerRuntime:
    LANES = ("chat", "tts", "vlm", "yapping")

    def __init__(self, maxsize: int = 32, start: bool = True):
        self.queues = {name: queue.Queue(maxsize=maxsize) for name in self.LANES}
        self._stop = threading.Event()
        self._threads = []
        if start:
            for name in self.LANES:
                thread = threading.Thread(target=self._run, args=(name,), daemon=True, name=f"ponyo-{name}-worker")
                thread.start()
                self._threads.append(thread)

    def submit(self, lane: str, task: Callable, *args, callback=None, **kwargs) -> bool:
        if lane not in self.queues or self._stop.is_set():
            return False
        try:
            self.queues[lane].put_nowait((task, args, kwargs, callback))
            return True
        except queue.Full:
            return False

    def submit_result(self, lane: str, task: Callable, callback: Callable, *args, **kwargs) -> bool:
        return self.submit(lane, task, *args, callback=callback, **kwargs)

    def get(self, lane: str, timeout=None):
        return self.queues[lane].get(timeout=timeout)

    def _run(self, lane: str):
        q = self.queues[lane]
        while not self._stop.is_set():
            try:
                task, args, kwargs, callback = q.get(timeout=0.1)
            except queue.Empty:
                continue
            result = None
            try:
                result = task(*args, **kwargs)
            except Exception as exc:
                structured_logger.error(
                    "worker_task_failed",
                    lane=lane,
                    error=type(exc).__name__,
                )
            finally:
                if callback:
                    try:
                        callback(result)
                    except Exception as exc:
                        structured_logger.error(
                            "worker_callback_failed",
                            lane=lane,
                            error=type(exc).__name__,
                        )
                q.task_done()

    def stop(self):
        self._stop.set()
        for thread in self._threads:
            thread.join(timeout=0.5)
        self._threads.clear()

    def clear_lane(self, lane: str) -> int:
        """Drop stale low-priority work, preserving lane isolation."""
        if lane not in self.queues:
            return 0
        q = self.queues[lane]
        dropped = 0
        while True:
            try:
                q.get_nowait()
                q.task_done()
                dropped += 1
            except queue.Empty:
                return dropped

    def queue_sizes(self):
        return {name: q.qsize() for name, q in self.queues.items()}
