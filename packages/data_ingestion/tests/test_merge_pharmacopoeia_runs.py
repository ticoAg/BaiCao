import json
from pathlib import Path

from data_ingestion.cli.merge_pharmacopoeia_runs import merge_runs, write_merge_outputs


def _write_run(root: Path, name: str, generated_at: str, records: list[dict], outcomes: list[dict]) -> None:
    run_dir = root / name / "manual-run"
    run_dir.mkdir(parents=True)
    (run_dir / "graph_import_records.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in records),
        encoding="utf-8",
    )
    (run_dir / "validated_extractions.jsonl").write_text(
        "".join(json.dumps(item, ensure_ascii=False) + "\n" for item in outcomes),
        encoding="utf-8",
    )
    (run_dir / "summary.json").write_text(
        json.dumps({"generated_at": generated_at, "entries_succeeded": sum(1 for item in outcomes if item["status"] == "success")}),
        encoding="utf-8",
    )


def test_later_run_wins_and_stats_count_entries(tmp_path: Path):
    runs = tmp_path / "runs"
    _write_run(
        runs,
        "full",
        "2026-04-19T10:00:00",
        [
            {"node_type": "药材", "node_name": "人参", "source": "huggingface", "properties": {"entry_title": "人参", "latin_name": "OLD"}},
            {"node_type": "病证", "node_name": "气虚", "source": "huggingface", "properties": {"entry_title": "人参"}},
        ],
        [{"entry_key": "人参:1-10", "entry_title": "人参", "status": "success"}],
    )
    _write_run(
        runs,
        "retry",
        "2026-04-19T20:00:00",
        [
            {"node_type": "药材", "node_name": "人参", "source": "huggingface", "properties": {"entry_title": "人参", "latin_name": "NEW"}},
            {"node_type": "药材", "node_name": "甘草", "source": "huggingface", "properties": {"entry_title": "甘草"}},
        ],
        [
            {"entry_key": "人参:1-10", "entry_title": "人参", "status": "success"},
            {"entry_key": "甘草:11-20", "entry_title": "甘草", "status": "llm_request_failed", "error_message": "timeout"},
        ],
    )
    result = merge_runs(runs)
    names = {(record.node_type, record.node_name): record for record in result.records}
    assert set(names) == {("药材", "人参"), ("病证", "气虚"), ("药材", "甘草")}
    assert names[("药材", "人参")].properties["latin_name"] == "NEW"
    assert names[("药材", "人参")].unit_id == "entry:人参"
    assert result.entries_succeeded == 1
    assert result.entries_failed == 1
    assert result.failed_entries[0]["entry_key"] == "甘草:11-20"

    out = tmp_path / "latest"
    write_merge_outputs(result, out)
    stats = json.loads((out / "stats.json").read_text(encoding="utf-8"))
    assert stats["entries_succeeded"] == 1
    assert stats["entries_failed"] == 1
    failures = [json.loads(line) for line in (out / "failures.jsonl").read_text(encoding="utf-8").splitlines() if line.strip()]
    assert failures[0]["status"] == "unrecoverable"
