import pytest

from knowledge_model.constants import EdgeType as SharedEdgeType
from knowledge_model.constants import NodeStatus, NodeType

from app.models.enums import EdgeType as ApiEdgeType
from app.schemas.graph import BaseNode, HerbNode

pytestmark = pytest.mark.contract


def test_herb_node_annotation_uses_shared_node_type():
    assert HerbNode.model_fields["type"].annotation is NodeType


def test_base_node_status_annotation_uses_shared_node_status():
    assert BaseNode.model_fields["status"].annotation is NodeStatus


def test_api_edge_type_keeps_shared_subset():
    api_edge_values = {edge.value for edge in ApiEdgeType}
    shared_edge_values = {edge.value for edge in SharedEdgeType}
    assert shared_edge_values <= api_edge_values
