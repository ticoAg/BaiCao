from data_ingestion.routing import FileRouteKey, ProcessorRegistry


def test_registry_prefers_exact_file_match():
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
