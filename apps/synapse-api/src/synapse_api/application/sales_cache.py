import logging
import time
from collections.abc import Callable, Hashable
from typing import Any

from synapse_api.domain.errors import SapUnavailable

logger = logging.getLogger(__name__)


class SalesCache:
    def __init__(self, seconds: float, clock: Callable[[], float] = time.monotonic):
        self.seconds = seconds
        self.clock = clock
        self.entries: dict[Hashable, tuple[float, Any]] = {}

    def get(self, key: Hashable, load: Callable[[], Any]) -> Any:
        stored = self.entries.get(key)
        if stored and self.clock() - stored[0] < self.seconds:
            return stored[1]
        try:
            value = load()
        except SapUnavailable:
            if stored is None:
                raise
            logger.warning("SAP unavailable, serving stale value for %s", key)
            return stored[1]
        self.entries[key] = (self.clock(), value)
        return value
