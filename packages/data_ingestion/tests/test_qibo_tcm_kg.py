from __future__ import annotations

import json
from pathlib import Path

import pytest

from data_ingestion.cli.qibo_tcm_kg_clean import main
from data_ingestion.qibo_tcm_kg import (
    DEFAULT_BATCH_ID,
    DEFAULT_FANGJI_PATH,
    DEFAULT_ZHONGYAO_PATH,
    IMPORT_SCOPE_KEY,
    PROMPT_HASH,
    SOURCE_ID,
    clean_relation_files,
    clean_relations,
    parse_endpoint,
    repo_root,
    write_clean_outputs,
)


def herb(name: str) -> str:
    return f"中药名\t{name}"


def formula_name(name: str) -> str:
    return f"方名\t{name}"


def prescription(name: str) -> str:
    return f"处方\t{name}"


def rel(node_1: str, relation: str, node_2: str) -> dict[str, str]:
    return {"node_1": node_1, "relation": relation, "node_2": node_2}


def by_key(records) -> dict[tuple[str, str], object]:
    return {(item.node_type, item.node_name): item for item in records}


def herb_fixture() -> list[dict[str, str]]:
    return [
        rel("中药材\t中药材", "include", herb("艾叶")),
        rel(herb("艾叶"), "another name", "别名\t蕲艾"),
        rel(herb("艾叶"), "another name", "别名\t香艾"),
        rel(herb("艾叶"), "distribution area", "分布\t东北"),
        rel(herb("艾叶"), "distribution area", "分布\t华北"),
        rel(herb("艾叶"), "functions", "功能\t温经"),
        rel(herb("艾叶"), "attending", "主治\t痛经"),
        rel(herb("艾叶"), "four properties", "四气\t温"),
        rel(herb("艾叶"), "five flavors", "五味\t苦"),
        rel(herb("艾叶"), "channel tropism", "归经\t脾"),
        rel(herb("艾叶"), "from", "来源\t中国药典"),
    ]


def formula_fixture() -> list[dict[str, str]]:
    return [
        rel("方剂\t方剂", "include", formula_name("同名方")),
        rel(formula_name("同名方"), "prescription type", prescription("同名方_1")),
        rel(formula_name("同名方"), "prescription type", prescription("同名方_2")),
        rel(formula_name("同名方"), "another name", "别名\t别称甲"),
        rel(formula_name("同名方"), "from", "来源\t伤寒论"),
        rel(prescription("同名方_1"), "composition", herb("当归")),
        rel(herb("当归"), "dose", "剂量\t10克"),
        rel(prescription("同名方_1"), "composition", herb("艾叶")),
        rel(herb("艾叶"), "dose", "剂量\t6克"),
        rel(prescription("同名方_1"), "functions", "功能主治\t补血"),
        rel(prescription("同名方_2"), "composition", herb("当归")),
        rel(herb("当归"), "dose", "剂量\t20克"),
        rel(prescription("同名方_2"), "composition", herb("甘草")),
    ]


def test_parse_endpoint_requires_exactly_one_tab():
    endpoint = parse_endpoint("中药名\t当归")
    assert endpoint.kind == "中药名"
    assert endpoint.name == "当归"
    with pytest.raises(ValueError, match="invalid endpoint"):
        parse_endpoint("当归")
    with pytest.raises(ValueError, match="invalid endpoint"):
        parse_endpoint("中药名\t")
    with pytest.raises(ValueError, match="invalid endpoint"):
        parse_endpoint("\t当归")
    with pytest.raises(ValueError, match="invalid endpoint"):
        parse_endpoint("中药名\t当\t归")


def test_unknown_relation_bad_endpoint_and_extra_keys_fail():
    with pytest.raises(ValueError, match="unknown relation"):
        clean_relations(
            [rel(herb("艾叶"), "toxicity", "毒性\t有毒")],
            [],
        )
    with pytest.raises(ValueError, match="invalid endpoint"):
        clean_relations(
            [rel("艾叶", "functions", "功能\t温经")],
            [],
        )
    with pytest.raises(ValueError, match="invalid relation keys"):
        clean_relations(
            [
                {
                    "node_1": herb("艾叶"),
                    "relation": "functions",
                    "node_2": "功能\t温经",
                    "extra": "1",
                }
            ],
            [],
        )
    with pytest.raises(ValueError, match="uncontextualized dose"):
        clean_relations(
            [],
            [rel(herb("当归"), "dose", "剂量\t10克")],
        )


def test_aliases_and_origin_stay_on_herb_properties():
    records = clean_relations(herb_fixture(), [])
    aiye = by_key(records)[("药材", "艾叶")]
    assert aiye.properties["aliases"] == ["蕲艾", "香艾"]
    assert aiye.properties["origin"] == ["东北", "华北"]
    assert "alias" not in aiye.properties
    assert "distribution_areas" not in aiye.properties
    assert {(edge.type, edge.target) for edge in aiye.edges} == {
        ("具有功效", "温经"),
        ("治疗病证", "痛经"),
        ("具有性味", "温"),
        ("具有性味", "苦"),
        ("归于经脉", "脾"),
        ("来源于", "中国药典"),
    }
    assert ("别名", "蕲艾") not in by_key(records)
    assert ("分布", "东北") not in by_key(records)


def test_dosage_is_folded_from_following_context_not_global_herb_edge():
    records = clean_relations(herb_fixture(), formula_fixture())
    keyed = by_key(records)
    first = keyed[("方剂", "同名方_1")]
    second = keyed[("方剂", "同名方_2")]
    first_doses = {
        edge.target: edge.properties.get("dosage")
        for edge in first.edges
        if edge.type == "组成药材"
    }
    second_doses = {
        edge.target: edge.properties.get("dosage")
        for edge in second.edges
        if edge.type == "组成药材"
    }
    assert first_doses == {"当归": "10克", "艾叶": "6克"}
    assert second_doses == {"当归": "20克", "甘草": None}
    danggui = keyed[("药材", "当归")]
    assert danggui.edges == []
    assert all(record.node_type != "剂量" for record in records)
    assert all(
        edge.type != "组成药材" or record.node_type == "方剂"
        for record in records
        for edge in record.edges
    )


def test_same_formula_name_keeps_distinct_prescriptions_and_inherits_aliases():
    records = clean_relations([], formula_fixture())
    keyed = by_key(records)
    first = keyed[("方剂", "同名方_1")]
    second = keyed[("方剂", "同名方_2")]
    assert first is not second
    assert first.properties["formula_name"] == "同名方"
    assert second.properties["formula_name"] == "同名方"
    assert "base_formula_name" not in first.properties
    assert first.properties["aliases"] == ["别称甲"]
    assert second.properties["aliases"] == ["别称甲"]
    assert {edge.target for edge in first.edges if edge.type == "来源于"} == {"伤寒论"}
    assert {edge.target for edge in second.edges if edge.type == "来源于"} == {"伤寒论"}
    assert ("方剂", "同名方") not in keyed


def test_multi_prescription_multi_source_does_not_broadcast_origin_edges():
    records = clean_relations(
        [],
        [
            rel(formula_name("多源方"), "prescription type", prescription("多源方_1")),
            rel(formula_name("多源方"), "prescription type", prescription("多源方_2")),
            rel(formula_name("多源方"), "from", "来源\t伤寒论"),
            rel(formula_name("多源方"), "from", "来源\t金匮要略"),
            rel(prescription("多源方_1"), "composition", herb("当归")),
            rel(prescription("多源方_2"), "composition", herb("甘草")),
        ],
    )
    keyed = by_key(records)
    first = keyed[("方剂", "多源方_1")]
    second = keyed[("方剂", "多源方_2")]
    assert [edge for edge in first.edges if edge.type == "来源于"] == []
    assert [edge for edge in second.edges if edge.type == "来源于"] == []
    assert ("来源", "伤寒论") not in keyed
    assert ("来源", "金匮要略") not in keyed


def test_single_prescription_inherits_all_sources():
    records = clean_relations(
        [],
        [
            rel(formula_name("单方"), "prescription type", prescription("单方_1")),
            rel(formula_name("单方"), "from", "来源\t伤寒论"),
            rel(formula_name("单方"), "from", "来源\t金匮要略"),
            rel(prescription("单方_1"), "composition", herb("当归")),
        ],
    )
    formula = by_key(records)[("方剂", "单方_1")]
    assert {edge.target for edge in formula.edges if edge.type == "来源于"} == {
        "伤寒论",
        "金匮要略",
    }


def test_conflicting_edge_properties_fail_and_duplicates_dedupe():
    duplicates = [
        rel(formula_name("甲方"), "prescription type", prescription("甲方_1")),
        rel(prescription("甲方_1"), "composition", herb("当归")),
        rel(herb("当归"), "dose", "剂量\t10克"),
        rel(prescription("甲方_1"), "composition", herb("当归")),
        rel(herb("当归"), "dose", "剂量\t10克"),
    ]
    records = clean_relations([], duplicates)
    edges = [
        edge
        for edge in by_key(records)[("方剂", "甲方_1")].edges
        if edge.type == "组成药材"
    ]
    assert len(edges) == 1
    assert edges[0].properties["dosage"] == "10克"

    conflict = [
        rel(formula_name("乙方"), "prescription type", prescription("乙方_1")),
        rel(prescription("乙方_1"), "composition", herb("当归")),
        rel(herb("当归"), "dose", "剂量\t10克"),
        rel(prescription("乙方_1"), "composition", herb("当归")),
        rel(herb("当归"), "dose", "剂量\t20克"),
    ]
    with pytest.raises(ValueError, match="conflict"):
        clean_relations([], conflict)


def test_edge_targets_have_independent_records_and_no_fabricated_evidence():
    records = clean_relations(herb_fixture(), formula_fixture())
    keyed = by_key(records)
    expected_targets = {
        ("药材", "艾叶"),
        ("药材", "当归"),
        ("药材", "甘草"),
        ("功效", "温经"),
        ("病证", "痛经"),
        ("病证", "补血"),
        ("性味", "温"),
        ("性味", "苦"),
        ("归经", "脾"),
        ("来源", "中国药典"),
        ("来源", "伤寒论"),
        ("方剂", "同名方_1"),
        ("方剂", "同名方_2"),
    }
    assert expected_targets <= set(keyed)
    for record in records:
        for edge in record.edges:
            target_type = {
                "具有功效": "功效",
                "治疗病证": "病证",
                "具有性味": "性味",
                "归于经脉": "归经",
                "来源于": "来源",
                "组成药材": "药材",
            }[edge.type]
            assert (target_type, edge.target) in keyed
        assert record.evidence_text is None
        assert record.node_type != "证据"
        assert record.prompt_hash == PROMPT_HASH
        assert "alias" not in record.properties
        record.validate_types()


def test_output_is_stable_and_fixture_counts_lock():
    first = clean_relations(herb_fixture(), formula_fixture())
    second = clean_relations(herb_fixture(), formula_fixture())
    assert [item.model_dump(exclude_none=True) for item in first] == [
        item.model_dump(exclude_none=True) for item in second
    ]
    composition = [
        edge
        for record in first
        for edge in record.edges
        if edge.type == "组成药材"
    ]
    assert len(composition) == 4
    assert sum(1 for edge in composition if edge.properties.get("dosage")) == 3
    assert all(item.source_id == SOURCE_ID for item in first)
    assert all(item.batch_id == DEFAULT_BATCH_ID for item in first)
    assert all(item.import_scope_key == IMPORT_SCOPE_KEY for item in first)
    assert all(item.prompt_hash == PROMPT_HASH for item in first)


def test_default_raw_paths_resolve_from_repo_root():
    root = repo_root()
    assert DEFAULT_ZHONGYAO_PATH == (
        root
        / ".cache/github/fengxi177/Knowlegde_Graph_TCM/zhongyao/data_zhongyao/relations_zhongyao.json"
    )
    assert DEFAULT_FANGJI_PATH == (
        root
        / ".cache/github/fengxi177/Knowlegde_Graph_TCM/fangji/data_fangji/relations_fangji.json"
    )


def test_cli_writes_records_and_stats(tmp_path: Path):
    zhongyao = tmp_path / "relations_zhongyao.json"
    fangji = tmp_path / "relations_fangji.json"
    out_dir = tmp_path / "out"
    zhongyao.write_text(json.dumps(herb_fixture(), ensure_ascii=False), encoding="utf-8")
    fangji.write_text(json.dumps(formula_fixture(), ensure_ascii=False), encoding="utf-8")
    main(
        [
            "--zhongyao",
            str(zhongyao),
            "--fangji",
            str(fangji),
            "--out-dir",
            str(out_dir),
        ]
    )
    records_path = out_dir / "records.jsonl"
    stats_path = out_dir / "stats.json"
    lines = [json.loads(line) for line in records_path.read_text(encoding="utf-8").splitlines()]
    stats = json.loads(stats_path.read_text(encoding="utf-8"))
    assert lines
    assert stats["source_ids"] == [SOURCE_ID]
    assert stats["batch_ids"] == [DEFAULT_BATCH_ID]
    assert stats["record_count"] == len(lines)
    assert stats["edge_type_counts"]["组成药材"] == 4
    assert all(item["prompt_hash"] == PROMPT_HASH for item in lines)


@pytest.mark.skipif(
    not DEFAULT_ZHONGYAO_PATH.is_file() or not DEFAULT_FANGJI_PATH.is_file(),
    reason="local Knowlegde_Graph_TCM relations missing",
)
def test_full_source_keeps_composition_dosage_and_safe_source_counts():
    records = clean_relation_files(DEFAULT_ZHONGYAO_PATH, DEFAULT_FANGJI_PATH)
    composition = [
        edge
        for record in records
        for edge in record.edges
        if edge.type == "组成药材"
    ]
    originated = [
        edge
        for record in records
        for edge in record.edges
        if edge.type == "来源于"
    ]
    assert sum(1 for record in records if record.node_type == "方剂") == 742
    assert len(composition) == 6521
    assert sum(1 for edge in composition if edge.properties.get("dosage")) == 5784
    assert len(originated) == 436
    assert len({(record.node_type, record.node_name) for record in records}) == len(records)
    assert all(record.evidence_text is None for record in records)
    assert all(record.prompt_hash == PROMPT_HASH for record in records)
    for record in records:
        assert "alias" not in record.properties
        assert "base_formula_name" not in record.properties
        assert "distribution_areas" not in record.properties
        record.validate_types()


def test_write_outputs_roundtrip(tmp_path: Path):
    records = clean_relations(herb_fixture(), formula_fixture())
    summary = write_clean_outputs(records, tmp_path)
    assert Path(summary["records"]).is_file()
    assert Path(summary["stats"]).is_file()
