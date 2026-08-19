from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))


from knowledge_model.constants import (
    EDGE_TYPE_TO_NEO4J_REL,
    NEO4J_REL_TO_EDGE_TYPE,
    EdgeType,
    NodeStatus,
    NodeType,
    parse_edge_type,
    parse_node_type,
    to_neo4j_label,
)
from knowledge_model.labels import EDGE_TYPE_LABELS, NODE_TYPE_LABELS


def test_node_type_has_herb_literal():
    assert NodeType.HERB == "药材"


def test_edge_type_has_contains_literal():
    assert EdgeType.CONTAINS == "包含成分"


def test_node_status_defaults_include_pending():
    assert NodeStatus.PENDING == "pending"


def test_node_type_exposes_chinese_label():
    assert NODE_TYPE_LABELS[NodeType.HERB] == "药材"


def test_edge_type_exposes_chinese_label():
    assert EDGE_TYPE_LABELS[EdgeType.HAS_EFFICACY] == "具有功效"


def test_node_type_exposes_prepared_piece_and_evidence():
    assert NodeType.PREPARED_HERB == "饮片"
    assert NodeType.EVIDENCE == "证据"
    assert NodeType.FORMULA == "方剂"


def test_edge_type_exposes_chinese_content_relations():
    assert EdgeType.HAS_PREPARED_FORM == "具有饮片"
    assert EdgeType.SUPPORTED_BY == "由证据支持"


def test_edge_type_uses_chinese_literals():
    assert EdgeType.HAS_EFFICACY == "具有功效"
    assert EdgeType.HAS_FLAVOR == "具有性味"
    assert EdgeType.ENTERS_MERIDIAN == "归于经脉"
    assert EdgeType.TREATS == "治疗病证"
    assert EdgeType.RELATED_HERB == "关联药材"
    assert EdgeType.RELATED_TREATMENT_METHOD == "关联治法"
    assert EdgeType.RELATED_SYNDROME == "关联证候"


def test_edge_type_has_neo4j_relation_mapping():
    assert EDGE_TYPE_TO_NEO4J_REL[EdgeType.CONTAINS] == "包含成分"
    assert EDGE_TYPE_TO_NEO4J_REL[EdgeType.HAS_EFFICACY] == "具有功效"
    assert EDGE_TYPE_TO_NEO4J_REL[EdgeType.TREATS] == "治疗病证"
    assert EDGE_TYPE_TO_NEO4J_REL[EdgeType.RELATED_HERB] == "关联药材"
    assert EDGE_TYPE_TO_NEO4J_REL[EdgeType.RELATED_TREATMENT_METHOD] == "关联治法"
    assert EDGE_TYPE_TO_NEO4J_REL[EdgeType.RELATED_SYNDROME] == "关联证候"
    assert NEO4J_REL_TO_EDGE_TYPE["具有性味"] == EdgeType.HAS_FLAVOR


def test_parse_edge_type_accepts_chinese_and_neo4j_relation_names():
    assert parse_edge_type("具有性味") == EdgeType.HAS_FLAVOR
    assert parse_edge_type("具有功效") == EdgeType.HAS_EFFICACY


def test_neo4j_labels_are_chinese():
    assert to_neo4j_label(NodeType.HERB) == "药材"
    assert to_neo4j_label("Herb") == "药材"
    assert parse_node_type("PreparedHerb") == NodeType.PREPARED_HERB
    assert parse_node_type("方剂") == NodeType.FORMULA


def test_case_formula_acupoint_types_exist():
    assert NodeType.FORMULA == "方剂"
    assert NodeType.MEDICAL_CASE == "医案"
    assert NodeType.ACUPOINT == "穴位"
    assert NodeType.TREATMENT_METHOD == "治法"
    assert EdgeType.CONTAINS_HERB == "组成药材"
    assert EdgeType.USES_FORMULA == "使用方剂"
    assert EdgeType.USES_ACUPOINT == "取用穴位"
    assert EdgeType.USES_METHOD == "采用治法"
    assert EdgeType.RECORDED_IN_CASE == "记载于医案"
    assert NODE_TYPE_LABELS[NodeType.FORMULA] == "方剂"
    assert EDGE_TYPE_TO_NEO4J_REL[EdgeType.CONTAINS_HERB] == "组成药材"
