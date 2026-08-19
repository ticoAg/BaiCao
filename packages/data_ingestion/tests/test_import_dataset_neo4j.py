from collections import Counter

from data_ingestion.cli.import_dataset_neo4j import find_existing, write_edges
from data_ingestion.dataset_records import DatasetEdge, DatasetRecord


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


def test_find_existing_does_not_merge_from_ambiguous_alias_lists():
    tx = Tx()
    assert find_existing(tx, "药材", ["白芍"]) is None
    assert "n.aliases" not in tx.calls[0][0]


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
    assert set(params["target_labels"]) == {"药材", "饮片"}
    assert stats["edges"] == 1
