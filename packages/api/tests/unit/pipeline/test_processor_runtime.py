from app.pipeline.processor_runtime import build_processor_runtime


def test_runtime_resolves_pharmacopoeia_processor_for_cached_file(tmp_path):
    runtime = build_processor_runtime()
    source = tmp_path / "2022.txt"
    source.write_text("一枝黄花\nYizhihuanghua\nSOLIDAGINISHERBA\n", encoding="utf-8")

    context = runtime.build_file_context(
        provider="huggingface",
        dataset="ZJUFanLab/TCMChat-dataset-600k",
        file_path="pretrain/train/books/national_standard/2022年中药药典.txt",
        local_abspath=str(source),
    )
    processor = runtime.resolve_processor(context)

    assert processor.route_key.file_path.endswith("2022年中药药典.txt")
