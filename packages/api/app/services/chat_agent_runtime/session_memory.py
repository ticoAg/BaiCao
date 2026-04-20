from collections.abc import Callable
from typing import Protocol

from langgraph.checkpoint.memory import InMemorySaver


class ThreadDeleteProtocol(Protocol):
    def delete_thread(self, thread_id: str) -> None: ...


class InMemorySessionManager:
    def __init__(
        self,
        *,
        checkpointer: ThreadDeleteProtocol | None = None,
        ttl_seconds: float = 1_800.0,
        time_fn: Callable[[], float] | None = None,
    ) -> None:
        self.checkpointer = checkpointer or InMemorySaver()
        self.ttl_seconds = ttl_seconds
        self.time_fn = time_fn or __import__("time").time
        self._last_seen: dict[str, float] = {}

    def touch(self, session_id: str) -> None:
        now = self.time_fn()
        self.evict_expired(now=now)
        self._last_seen[session_id] = now

    def evict_expired(self, *, now: float | None = None) -> None:
        current_time = self.time_fn() if now is None else now
        expired = [
            session_id
            for session_id, last_seen_at in self._last_seen.items()
            if current_time - last_seen_at > self.ttl_seconds
        ]
        for session_id in expired:
            self.checkpointer.delete_thread(session_id)
            del self._last_seen[session_id]
