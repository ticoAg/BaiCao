from collections import Counter

import pytest

from data_ingestion.cli import import_dataset_neo4j as importer
from data_ingestion.cli.import_dataset_neo4j import NodeCache, find_existing, write_edges
from data_ingestion.dataset_records import DatasetEdge, DatasetRecord
from data_ingestion.provenance import slim_record


class Result:
    def __init__(self, rows=None):
        self.rows = rows or []

    def __iter__(self):
        return iter(self.rows)

    def single(self):
        return {"rel": "组成药材"}


class Tx:
    def __init__(self):
        self.calls = []

    def run(self, query, **params):
        self.calls.append((query, params))
        return Result()


def test_node_cache_finds_exact_name_and_alias():
    cache = NodeCache()
    cache.by_label_name[("药材", "人参")] = {"eid": "e1", "props": {"名称": "人参", "别名": "棒槌"}}
    cache.by_label_alias[("药材", "棒槌")] = "人参"
    assert cache.find("药材", ["人参"], include_aliases=False)["eid"] == "e1"
    assert cache.find("药材", ["棒槌"], include_aliases=False) is None
    assert cache.find("药材", ["棒槌"], include_aliases=True)["eid"] == "e1"
    assert cache.find("药材", ["黄芪"], include_aliases=True) is None


def test_find_existing_does_not_merge_from_ambiguous_alias_lists():
    tx = Tx()
    assert find_existing(tx, "药材", ["白芍"]) is None
    assert "n.名称 IN $names" in tx.calls[0][0]
    assert "n.aliases" not in tx.calls[1][0]
    assert "properties(n)[key]" in tx.calls[1][0]
    assert set(tx.calls[1][1]["lookup_keys"]) == {
        "name",
        "别名",
        "alias",
        "拼音",
        "pinyin_name",
        "拉丁名",
        "latin_name",
    }

    exact_only = Tx()
    assert find_existing(exact_only, "药材", ["白芍"], include_aliases=False) is None
    assert len(exact_only.calls) == 1


def test_write_edges_restricts_same_name_target_to_contract_labels():
    tx = Tx()
    record = DatasetRecord(
        source_id="fengxi177-knowledge-graph-tcm",
        batch_id="2026-08-19-kg-tcm-v1",
        unit_id="方剂:鳖甲",
        node_type="方剂",
        node_name="鳖甲",
        import_scope_key="github:fengxi177/Knowlegde_Graph_TCM",
        edges=[DatasetEdge(type="组成药材", target="鳖甲", properties={"dosage": "30克"})],
    )

    stats = Counter()
    write_edges(tx, record, "鳖甲", stats)

    query, params = tx.calls[0]
    assert "labels(target)" in query
    assert "properties(target)[key]" in query
    assert set(params["target_labels"]) == {"药材", "饮片"}
    assert stats["edges"] == 1


def test_write_edges_uses_resolved_target_name_and_static_label():
    tx = Tx()
    record = DatasetRecord(
        source_id="source",
        batch_id="batch",
        unit_id="病证:测试证",
        node_type="病证",
        node_name="测试证",
        edges=[DatasetEdge(type="关联药材", target="白芍")],
    )

    stats = Counter()
    write_edges(
        tx,
        record,
        "测试证",
        stats,
        resolved_targets={("药材", "白芍"): "芍药"},
    )

    query, params = tx.calls[0]
    assert "MATCH (target:药材)" in query
    assert "target.名称 = $resolved_target" in query
    assert params["resolved_target"] == "芍药"


def test_write_edges_persists_source_row_locator():
    tx = Tx()
    record = DatasetRecord(
        source_id="tcm-db",
        batch_id="batch",
        unit_id="病证:测试证",
        node_type="病证",
        node_name="测试证",
        edges=[
            DatasetEdge(
                type="关联症状",
                target="口干",
                properties={"evidence_ref": "tcm_knowledge.db:syndrome_symptoms:1"},
            )
        ],
    )

    write_edges(tx, record, "测试证", Counter())

    query, params = tx.calls[0]
    assert "r.证据定位" in query
    assert params["evidence_ref"] == "tcm_knowledge.db:syndrome_symptoms:1"

    slimmed = slim_record(record, prompt_hash="sha256:test", import_scope_key="scope")
    assert slimmed.edges[0].properties["evidence_ref"] == params["evidence_ref"]


def test_write_edges_persists_dosage_ratio():
    tx = Tx()
    record = DatasetRecord(
        source_id="tcm-mkg",
        batch_id="batch",
        unit_id="方剂:测试方",
        node_type="方剂",
        node_name="测试方",
        edges=[
            DatasetEdge(
                type="组成药材",
                target="黄芪",
                properties={"dosage_ratio": "0.5"},
            )
        ],
    )

    write_edges(tx, record, "测试方", Counter())

    query, params = tx.calls[0]
    assert "r.剂量比例" in query
    assert params["dosage_ratio"] == "0.5"


@pytest.mark.parametrize(
    ("edge_type", "target", "target_label"),
    [
        ("适用于", "霍乱", "病证"),
        ("关联证候", "心经积热证", "病证"),
        ("关联症状", "口干", "症状"),
        ("关联药材", "仙茅", "药材"),
        ("关联治法", "温阳散寒", "治法"),
    ],
)
def test_write_related_edges_restrict_target_labels(edge_type, target, target_label):
    tx = Tx()
    record = DatasetRecord(
        source_id="shennong-tcm-kg",
        batch_id="2026-08-19-shennong-tcm-kg-v1",
        unit_id="病证:腹痛",
        node_type="病证",
        node_name="腹痛",
        import_scope_key="github:michael-wzhu/ShenNong-TCM-LLM:src/TCM-KG_triples.txt",
        edges=[DatasetEdge(type=edge_type, target=target)],
    )

    stats = Counter()
    write_edges(tx, record, "腹痛", stats)

    assert tx.calls[0][1]["target_labels"] == [target_label]
    assert stats["edges"] == 1


def test_import_records_batches_node_and_edge_transactions(monkeypatch):
    class Session:
        def __init__(self):
            self.calls = []

        def __enter__(self):
            return self

        def __exit__(self, *_args):
            return None

        def run(self, query, **params):
            return []

        def execute_write(self, func, batch, *args):
            self.calls.append((func.__name__, len(batch)))
            return func(None, batch, *args)

    class Driver:
        def __init__(self):
            self.session_instance = Session()

        def session(self, *, database):
            assert database == "neo4j"
            return self.session_instance

    def write_node_batch(_tx, batch, _preexisting_labels, _cache=None):
        return [(record, record.node_name) for record in batch], Counter(
            created=len(batch)
        )

    def write_edge_batch(_tx, batch, _resolved_targets):
        return Counter(edges=len(batch))

    monkeypatch.setattr(importer, "_write_node_batch", write_node_batch)
    monkeypatch.setattr(importer, "_write_edge_batch", write_edge_batch)
    monkeypatch.setattr(importer, "_preexisting_labels", lambda _session, _records: set())
    records = [
        DatasetRecord(
            source_id="source",
            batch_id="batch",
            unit_id=f"病证:{index}",
            node_type="病证",
            node_name=f"病证{index}",
            edges=(
                [DatasetEdge(type="关联药材", target="药材")]
                if index != 4
                else []
            ),
        )
        for index in range(5)
    ]
    driver = Driver()

    stats = importer.import_records(records, driver, batch_size=2)

    assert driver.session_instance.calls == [
        ("write_node_batch", 2),
        ("write_node_batch", 2),
        ("write_node_batch", 1),
        ("write_edge_batch", 2),
        ("write_edge_batch", 2),
    ]
    assert stats == {"skipped_records": 0, "created": 5, "edges": 4}
