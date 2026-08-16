from data_ingestion.dataset_records import compute_stats, stamp_import_record


def test_stamp_and_stats_keep_source_and_batch():
    record = stamp_import_record(
        {
            "node_type": "药材",
            "node_name": "艾绒",
            "source": "daoyi-suyang",
            "status": "pending",
            "properties": {},
            "edges": [{"type": "治疗病证", "target": "痛症", "properties": {}}],
        },
        source_id="daoyi-suyang",
        batch_id="2026-08-16-suyang-b01",
        unit_id="chapter-001",
        processor="test",
        unit_title="第1章 苏子阳",
        extracted_at="2026-08-16T00:00:00+00:00",
    )
    stats = compute_stats([record])
    assert record.source_id == "daoyi-suyang"
    assert record.batch_id == "2026-08-16-suyang-b01"
    assert record.properties["import_batch_id"] == "2026-08-16-suyang-b01"
    assert stats["record_count"] == 1
    assert stats["node_type_counts"]["药材"] == 1
    assert stats["edge_type_counts"]["治疗病证"] == 1
    assert stats["by_batch"]["2026-08-16-suyang-b01"]["record_count"] == 1
