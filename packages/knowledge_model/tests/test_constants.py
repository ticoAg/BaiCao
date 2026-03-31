from pathlib import Path
import sys


PACKAGE_ROOT = Path(__file__).resolve().parents[1]
if str(PACKAGE_ROOT) not in sys.path:
    sys.path.insert(0, str(PACKAGE_ROOT))


from knowledge_model.constants import EdgeType, NodeStatus, NodeType
from knowledge_model.labels import EDGE_TYPE_LABELS, NODE_TYPE_LABELS


def test_node_type_has_herb_literal():
    assert NodeType.HERB == "药材"


def test_edge_type_has_contains_literal():
    assert EdgeType.CONTAINS == "CONTAINS"


def test_node_status_defaults_include_pending():
    assert NodeStatus.PENDING == "pending"


def test_node_type_exposes_chinese_label():
    assert NODE_TYPE_LABELS[NodeType.HERB] == "药材"


def test_edge_type_exposes_chinese_label():
    assert EDGE_TYPE_LABELS[EdgeType.HAS_EFFICACY] == "具有功效"


def test_node_type_exposes_prepared_piece_and_evidence():
    assert NodeType.PREPARED_HERB == "饮片"
    assert NodeType.EVIDENCE == "证据"


def test_edge_type_exposes_chinese_content_relations():
    assert EdgeType.HAS_PREPARED_FORM == "具有饮片"
    assert EdgeType.SUPPORTED_BY == "由证据支持"
