from app.services.chat_agent_runtime.session_memory import InMemorySessionManager


class _FakeCheckpointer:
    def __init__(self) -> None:
        self.deleted: list[str] = []

    def delete_thread(self, thread_id: str) -> None:
        self.deleted.append(thread_id)


def test_session_manager_evicts_expired_threads_before_touching_current_session():
    now = 2_000.0
    checkpointer = _FakeCheckpointer()
    manager = InMemorySessionManager(
        checkpointer=checkpointer,
        ttl_seconds=1_800.0,
        time_fn=lambda: now,
    )
    manager._last_seen = {  # noqa: SLF001 - precise TTL behavior test
        "expired-session": now - 1_801.0,
        "fresh-session": now - 60.0,
    }

    manager.touch("current-session")

    assert checkpointer.deleted == ["expired-session"]
    assert "expired-session" not in manager._last_seen  # noqa: SLF001 - precise TTL behavior test
    assert manager._last_seen["fresh-session"] == now - 60.0  # noqa: SLF001 - precise TTL behavior test
    assert manager._last_seen["current-session"] == now  # noqa: SLF001 - precise TTL behavior test
