from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))


from graph_schema.constants import EdgeType, NodeType
from graph_schema.import_records import GraphImportEdge, GraphImportRecord
from graph_schema.node_models import (
    EvidenceNodeModel,
    HerbNodeModel,
    PreparedHerbNodeModel,
    SymptomNodeModel,
)


def test_graph_import_record_accepts_known_node_type():
    record = GraphImportRecord(
        node_type=NodeType.HERB,
        node_name="陈皮",
        source="中国药典",
    )

    assert record.node_name == "陈皮"
    assert record.node_type == NodeType.HERB


def test_graph_import_record_accepts_known_edge_type():
    record = GraphImportRecord(
        node_type=NodeType.HERB,
        node_name="陈皮",
        source="中国药典",
        edges=[
            GraphImportEdge(
                type=EdgeType.HAS_EFFICACY,
                target="理气健脾",
                properties={},
            )
        ],
    )

    assert record.edges[0].type == EdgeType.HAS_EFFICACY


def test_herb_node_model_uses_english_type_and_chinese_data():
    node = HerbNodeModel(
        id="herb-chenpi",
        name="陈皮",
        source="中国药典",
        herb_type="base",
        category="理气药",
    )

    assert node.type == NodeType.HERB
    assert node.name == "陈皮"


def test_shared_models_expose_field_descriptions_in_json_schema():
    herb_schema = HerbNodeModel.model_json_schema()
    import_record_schema = GraphImportRecord.model_json_schema()
    import_edge_schema = GraphImportEdge.model_json_schema()

    assert herb_schema["properties"]["source"]["description"] == "数据来源"
    assert herb_schema["properties"]["status"]["description"] == "节点审核状态"
    assert herb_schema["properties"]["category"]["description"] == "药材分类"
    assert import_record_schema["properties"]["edges"]["description"] == "与当前节点关联的边列表"
    assert import_edge_schema["properties"]["target"]["description"] == "目标节点名称或标识"


def test_prepared_herb_node_model_accepts_parent_reference():
    node = PreparedHerbNodeModel(
        id="饮片:一枝黄花饮片",
        name="一枝黄花饮片",
        source="huggingface",
        prepared_from_herb="一枝黄花",
    )

    assert node.type == NodeType.PREPARED_HERB
    assert node.prepared_from_herb == "一枝黄花"


def test_symptom_node_model_keeps_symptom_separate_from_disease():
    node = SymptomNodeModel(
        id="症状:口干",
        name="口干",
        source="tcm-db",
        category="问诊",
        description="自觉口渴或口腔干燥",
    )

    assert node.type == NodeType.SYMPTOM
    assert node.category == "问诊"


def test_evidence_node_model_requires_source_location_fields():
    node = EvidenceNodeModel(
        id="证据:test",
        name="一枝黄花条目证据",
        source="huggingface",
        raw_text="一枝黄花\nYizhihuanghua",
        source_provider="huggingface",
        dataset_name="ZJUFanLab/TCMChat-dataset-600k",
        file_path="pretrain/train/books/national_standard/2022年中药药典.txt",
        entry_title="一枝黄花",
        line_start=1,
        line_end=21,
        chunk_hash="abc123",
    )

    assert node.type == NodeType.EVIDENCE
    assert node.file_path.endswith("2022年中药药典.txt")
