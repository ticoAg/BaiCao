import asyncio
import time
from collections.abc import AsyncIterator, Callable
from contextlib import asynccontextmanager


class InMemorySessionManager:
    def __init__(
        self,
        *,
        on_evict: Callable[[str], None] | None = None,
        ttl_seconds: float = 1_800.0,
        time_fn: Callable[[], float] | None = None,
    ) -> None:
        self.on_evict = on_evict
        self.ttl_seconds = ttl_seconds
        self.time_fn = time_fn or time.time
        self._last_seen: dict[str, float] = {}
        self._locks: dict[str, asyncio.Lock] = {}
        self._active_counts: dict[str, int] = {}

    def touch(self, session_id: str) -> None:
        now = self.time_fn()
        self.evict_expired(now=now)
        self._last_seen[session_id] = now

    @asynccontextmanager
    async def session(self, session_id: str) -> AsyncIterator[None]:
        self.touch(session_id)
        lock = self._locks.setdefault(session_id, asyncio.Lock())
        self._active_counts[session_id] = self._active_counts.get(session_id, 0) + 1

        try:
            async with lock:
                yield
        finally:
            remaining = self._active_counts.get(session_id, 1) - 1
            if remaining > 0:
                self._active_counts[session_id] = remaining
            else:
                self._active_counts.pop(session_id, None)
            self._last_seen[session_id] = self.time_fn()

    def evict_expired(self, *, now: float | None = None) -> None:
        current_time = self.time_fn() if now is None else now
        expired = [
            session_id
            for session_id, last_seen_at in self._last_seen.items()
            if current_time - last_seen_at > self.ttl_seconds
            and self._active_counts.get(session_id, 0) == 0
        ]
        for session_id in expired:
            if self.on_evict is not None:
                self.on_evict(session_id)
            self._last_seen.pop(session_id, None)
            self._locks.pop(session_id, None)
