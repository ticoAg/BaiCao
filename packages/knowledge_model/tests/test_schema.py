from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))


from knowledge_model.constants import EdgeType, NodeType
from knowledge_model.import_records import GraphImportEdge, GraphImportRecord
from knowledge_model.node_models import HerbNodeModel


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
