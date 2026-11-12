"""Small JSON-lines logger for runtime failures and latency diagnostics."""
import json
import logging
import sys
import time
from typing import Callable, Optional


class StructuredLogger:
    def __init__(self, name: str = "ponyo", sink: Optional[Callable[[str], None]] = None):
        self._sink = sink
        self._logger = logging.getLogger(name)

    def log(self, level: int, event: str, **fields):
        safe = {}
        for key, value in fields.items():
            key_lower = key.lower()
            if any(word in key_lower for word in ("password", "token", "secret", "credential", "api_key", "connection")):
                safe[key] = "[REDACTED]"
            else:
                safe[key] = value
        payload = {"timestamp": time.strftime("%Y-%m-%dT%H:%M:%S%z"), "event": event, **safe}
        line = json.dumps(payload, ensure_ascii=False, default=str)
        if self._sink:
            self._sink(line)
        else:
            self._logger.log(level, line)

    def info(self, event: str, **fields):
        self.log(logging.INFO, event, **fields)

    def warning(self, event: str, **fields):
        self.log(logging.WARNING, event, **fields)

    def error(self, event: str, **fields):
        self.log(logging.ERROR, event, **fields)


structured_logger = StructuredLogger()
