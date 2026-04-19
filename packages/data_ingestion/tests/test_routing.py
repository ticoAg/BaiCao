"""覆盖来源文件路由注册表的精确匹配行为。"""

from data_ingestion.routing import FileRouteKey, ProcessorRegistry


def test_registry_prefers_exact_file_match():
    """验证注册表按 provider、dataset、file_path 精确解析处理器。"""

    registry = ProcessorRegistry()
    registry.register(
        FileRouteKey(
            provider="huggingface",
            dataset="ZJUFanLab/TCMChat-dataset-600k",
            file_path="pretrain/train/books/national_standard/2022年中药药典.txt",
        ),
        object,
    )

    resolved = registry.resolve(
        provider="huggingface",
        dataset="ZJUFanLab/TCMChat-dataset-600k",
        file_path="pretrain/train/books/national_standard/2022年中药药典.txt",
    )

    assert resolved is object
