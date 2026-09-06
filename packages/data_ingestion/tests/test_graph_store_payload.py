from data_ingestion.dataset_records import DatasetEdge, DatasetRecord
from data_ingestion.graph_store_payload import (
    for_graph_store,
    graph_store_records,
    write_admin_csvs,
)


def _record(*, node_type: str, node_name: str, **kwargs) -> DatasetRecord:
    payload = dict(
        source_id="tcm-ancient-books",
        batch_id="batch",
        unit_id=f"{node_type}:{node_name}",
        node_type=node_type,
        node_name=node_name,
        prompt_hash="sha256:test",
        import_scope_key="scope",
        edges=[],
        properties={},
    )
    payload.update(kwargs)
    return DatasetRecord(**payload)


def test_for_graph_store_drops_origin_edges_and_fragments():
    record = _record(
        node_type="药材",
        node_name="人参",
        evidence_text="人参甘温。",
        properties={"证据原文": "人参甘温。", "alias": "棒槌"},
        edges=[
            DatasetEdge(type="来源于", target="本草经"),
            DatasetEdge(type="具有功效", target="补气"),
        ],
    )
    payload = for_graph_store(record)
    assert payload.evidence_text is None
    assert "证据原文" not in payload.properties
    assert payload.properties["alias"] == "棒槌"
    assert [edge.type for edge in payload.edges] == ["具有功效"]


def test_graph_store_records_omit_source_nodes_and_collapse_names():
    records = [
        _record(
            node_type="来源",
            node_name="本草经",
            edges=[DatasetEdge(type="来源于", target="unused")],
        ),
        _record(
            node_type="药材",
            node_name="人参",
            edges=[DatasetEdge(type="来源于", target="本草经")],
        ),
        _record(
            node_type="药材",
            node_name="人参",
            properties={"性味": "甘温"},
            edges=[DatasetEdge(type="具有功效", target="补气")],
        ),
        _record(
            node_type="功效",
            node_name="补气",
        ),
    ]
    kept, stats = graph_store_records(records)
    names = {(record.node_type, record.node_name) for record in kept}
    assert ("来源", "本草经") not in names
    herb = next(record for record in kept if record.node_name == "人参")
    assert herb.properties["性味"] == "甘温"
    assert [edge.type for edge in herb.edges] == ["具有功效"]
    assert stats["source_edges"] == 2
    assert stats["omitted_records"] == 1
    assert stats["collapsed_records"] == 1


def test_include_source_graph_keeps_origin_and_fragments():
    record = _record(
        node_type="证据",
        node_name="证据:人参",
        evidence_text="人参甘温。",
        edges=[DatasetEdge(type="来源于", target="本草经")],
    )
    payload = for_graph_store(record, include_source_graph=True)
    assert payload.evidence_text == "人参甘温。"
    assert payload.edges[0].type == "来源于"


def test_write_admin_csvs_omits_origin_edges(tmp_path):
    records = [
        _record(
            node_type="方剂",
            node_name="四君子汤",
            evidence_text="人参白术。",
            edges=[
                DatasetEdge(type="来源于", target="本草经"),
                DatasetEdge(type="组成药材", target="人参"),
            ],
        ),
        _record(node_type="药材", node_name="人参"),
        _record(node_type="来源", node_name="本草经"),
    ]
    stats = write_admin_csvs(records, tmp_path)
    node_names = {path.name for path in (tmp_path / "nodes").glob("*.csv")}
    assert "来源.csv" not in node_names
    assert "方剂.csv" in node_names
    rel_text = (tmp_path / "rels" / "方剂-组成药材-药材.csv").read_text(encoding="utf-8")
    assert "组成药材" in rel_text
    assert "来源于" not in rel_text
    assert "人参白术" not in (tmp_path / "nodes" / "方剂.csv").read_text(encoding="utf-8")
    script = (tmp_path / "neo4j-admin.sh").read_text(encoding="utf-8")
    assert "/var/lib/neo4j/bin/neo4j-admin" in script
    assert "--overwrite-destination=true" in script
    assert '"${ROOT}/nodes/' in script
    assert stats["source_edges"] == 1
    assert stats["dangling_edges"] == 0


def test_admin_ids_keep_same_name_different_stable_ids_apart(tmp_path):
    records = [
        _record(node_type="药材", node_name="明党参", properties={"chp_id": "A"}),
        _record(node_type="药材", node_name="明党参", properties={"chp_id": "B"}),
    ]
    write_admin_csvs(records, tmp_path)
    text = (tmp_path / "nodes" / "药材.csv").read_text(encoding="utf-8")
    assert "药材:明党参:A" in text
    assert "药材:明党参:B" in text

