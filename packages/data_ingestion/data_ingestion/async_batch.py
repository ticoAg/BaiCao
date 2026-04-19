"""提供可复用的异步批量执行器。"""

from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable, Sequence
from typing import TypeVar


ItemT = TypeVar("ItemT")
ResultT = TypeVar("ResultT")
_MISSING = object()


async def run_async_batch(
    *,
    items: Sequence[ItemT],
    worker: Callable[[ItemT], Awaitable[ResultT]],
    concurrency: int = 1,
    on_result: Callable[[int, ItemT, ResultT], None] | None = None,
) -> list[ResultT]:
    """按给定并发度执行一组异步任务，并保证返回结果顺序与输入一致。"""

    semaphore = asyncio.Semaphore(max(1, concurrency))
    results: list[ResultT | object] = [_MISSING] * len(items)

    async def _run_one(index: int, item: ItemT) -> None:
        async with semaphore:
            result = await worker(item)
        results[index] = result
        if on_result is not None:
            on_result(index, item, result)

    await asyncio.gather(*[_run_one(index, item) for index, item in enumerate(items)])
    return [result for result in results if result is not _MISSING]
