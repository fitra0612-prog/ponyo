"""Low-overhead in-memory counters and percentile timings for live runtime."""
from collections import defaultdict, deque
import threading


class RuntimeMetrics:
    def __init__(self, history_size: int = 256):
        self.history_size = max(10, int(history_size))
        self._timings = defaultdict(lambda: deque(maxlen=self.history_size))
        self._counters = defaultdict(int)
        self._lock = threading.Lock()

    def increment(self, name: str, amount: int = 1) -> None:
        with self._lock:
            self._counters[str(name)] += int(amount)

    def observe(self, name: str, value: float) -> None:
        with self._lock:
            self._timings[str(name)].append(float(value))

    @staticmethod
    def _percentile(values, percentile: float) -> float:
        if not values:
            return 0.0
        ordered = sorted(values)
        rank = (len(ordered) - 1) * percentile
        low = int(rank)
        high = min(low + 1, len(ordered) - 1)
        fraction = rank - low
        return ordered[low] + (ordered[high] - ordered[low]) * fraction

    def snapshot(self) -> dict:
        with self._lock:
            counters = dict(self._counters)
            timings = {
                name: {
                    "count": len(values),
                    "last": round(values[-1], 2) if values else 0.0,
                    "p50": round(self._percentile(list(values), 0.50), 2),
                    "p95": round(self._percentile(list(values), 0.95), 2),
                    "p99": round(self._percentile(list(values), 0.99), 2),
                }
                for name, values in self._timings.items()
            }
        return {"counters": counters, "timings": timings}


runtime_metrics = RuntimeMetrics()
