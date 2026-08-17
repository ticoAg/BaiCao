from data_ingestion.cli.compute_dataset_stats import render_view


def test_render_view_uses_chinese_property_keys():
    text = render_view(
        "daoyi-suyang",
        {
            "record_count": 1,
            "unit_count": 1,
            "batch_ids": ["b1"],
            "generated_at": "2026-08-17T00:00:00+00:00",
            "node_type_counts": {"方剂": 1},
            "edge_type_counts": {"使用方剂": 1},
            "by_batch": {"b1": {"unit_count": 1, "record_count": 1}},
        },
        "manual:baicao-knowledge:daoyi-suyang",
    )
    assert "import_source_id" not in text
    assert "import_batch_id" not in text
    assert "n.导入源 = '道医苏子阳'" in text
    assert "人工:白草知识:道医苏子阳" in text


def test_render_view_localizes_pharmacopoeia_source():
    text = render_view(
        "national-standard-2022-pharmacopoeia",
        {
            "record_count": 1,
            "unit_count": 1,
            "batch_ids": [],
            "generated_at": "2026-08-17T00:00:00+00:00",
            "node_type_counts": {},
            "edge_type_counts": {},
            "by_batch": {},
        },
        "huggingface|ZJUFanLab/TCMChat-dataset-600k|pretrain/train/books/national_standard/2022年中药药典.txt",
    )
    assert "n.导入源 = '2022年中药药典'" in text
    assert "抱抱脸:中药药典2022" in text
