"""覆盖通用异步批量执行器的保序与回调行为。"""

import asyncio
import time

from data_ingestion.async_batch import run_async_batch


def test_run_async_batch_preserves_input_order_and_triggers_callback():
    """验证并发执行后返回结果仍按输入顺序排列，并触发逐条回调。"""

    callback_indexes: list[int] = []

    async def worker(item: int) -> str:
        await asyncio.sleep(0.02 * (3 - item))
        return f"item-{item}"

    def on_result(index: int, item: int, result: str) -> None:
        callback_indexes.append(index)
        assert result == f"item-{item}"

    results = asyncio.run(
        run_async_batch(
            items=[0, 1, 2],
            worker=worker,
            concurrency=3,
            on_result=on_result,
        )
    )

    assert results == ["item-0", "item-1", "item-2"]
    assert sorted(callback_indexes) == [0, 1, 2]


def test_run_async_batch_honors_concurrency_limit():
    """验证并发上限会影响总耗时，而不是串行执行全部任务。"""

    async def worker(item: int) -> int:
        await asyncio.sleep(0.05)
        return item

    started_at = time.perf_counter()
    results = asyncio.run(run_async_batch(items=[1, 2, 3, 4], worker=worker, concurrency=2))
    elapsed = time.perf_counter() - started_at

    assert results == [1, 2, 3, 4]
    assert 0.09 <= elapsed < 0.18
