import asyncio

import pytest

from app.services.chat_agent_runtime.session_memory import InMemorySessionManager


def test_session_manager_default_ttl_is_30_minutes():
    manager = InMemorySessionManager()
    assert manager.ttl_seconds == 1_800.0


def test_session_manager_evicts_expired_threads_before_touching_current_session():
    now = 2_000.0
    evicted: list[str] = []
    manager = InMemorySessionManager(
        on_evict=evicted.append,
        ttl_seconds=1_800.0,
        time_fn=lambda: now,
    )
    manager._last_seen = {  # noqa: SLF001 - precise TTL behavior test
        "expired-session": now - 1_801.0,
        "fresh-session": now - 60.0,
    }

    manager.touch("current-session")

    assert evicted == ["expired-session"]
    assert "expired-session" not in manager._last_seen  # noqa: SLF001 - precise TTL behavior test
    assert manager._last_seen["fresh-session"] == now - 60.0  # noqa: SLF001 - precise TTL behavior test
    assert manager._last_seen["current-session"] == now  # noqa: SLF001 - precise TTL behavior test


@pytest.mark.asyncio
async def test_session_manager_serializes_same_session_requests():
    manager = InMemorySessionManager(time_fn=lambda: 100.0)
    events: list[str] = []

    async def worker(name: str):
        async with manager.session("same-session"):
            events.append(f"{name}:enter")
            await asyncio.sleep(0.01)
            events.append(f"{name}:exit")

    await asyncio.gather(worker("first"), worker("second"))

    assert events == [
        "first:enter",
        "first:exit",
        "second:enter",
        "second:exit",
    ]


@pytest.mark.asyncio
async def test_session_manager_does_not_evict_active_session():
    now = 2_000.0
    evicted: list[str] = []
    manager = InMemorySessionManager(
        on_evict=evicted.append,
        ttl_seconds=1_800.0,
        time_fn=lambda: now,
    )

    entered = asyncio.Event()
    release = asyncio.Event()

    async def keep_session_active():
        async with manager.session("active-session"):
            manager._last_seen["active-session"] = now - 1_900.0  # noqa: SLF001 - active session eviction guard
            entered.set()
            await release.wait()

    task = asyncio.create_task(keep_session_active())
    await entered.wait()

    manager.touch("fresh-session")

    assert evicted == []
    release.set()
    await task
