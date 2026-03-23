import pytest

pytestmark = pytest.mark.contract


def test_graph_workbench_meta_summary_requires_database_counts():
    from app.schemas.graph_workbench import GraphWorkbenchMetaSummary

    summary = GraphWorkbenchMetaSummary.model_validate(
        {
            "node_count": 12,
            "relationship_count": 18,
            "label_count": 4,
            "relationship_type_count": 6,
            "property_key_count": 11,
            "index_count": 2,
            "constraint_count": 1,
            "truncated": False,
            "generated_at": "2026-03-23T10:00:00Z",
        }
    )

    assert summary.node_count == 12
    assert summary.relationship_count == 18
    assert summary.truncated is False


def test_graph_workbench_label_meta_requires_property_keys():
    from app.schemas.graph_workbench import GraphWorkbenchLabelMetaItem

    item = GraphWorkbenchLabelMetaItem.model_validate(
        {
            "name": "Herb",
            "count": 3,
            "property_keys": ["name", "category"],
        }
    )

    assert item.name == "Herb"
    assert item.property_keys == ["name", "category"]


def test_graph_workbench_schema_response_includes_indexes_and_constraints():
    from app.schemas.graph_workbench import (
        GraphWorkbenchSchemaConstraintItem,
        GraphWorkbenchSchemaIndexItem,
        GraphWorkbenchSchemaResponse,
    )

    response = GraphWorkbenchSchemaResponse.model_validate(
        {
            "indexes": [
                {
                    "name": "idx_herb_name",
                    "type": "RANGE",
                    "entity_type": "NODE",
                    "labels_or_types": ["Herb"],
                    "properties": ["name"],
                    "state": "ONLINE",
                }
            ],
            "constraints": [
                {
                    "name": "constraint_herb_name",
                    "type": "UNIQUENESS",
                    "entity_type": "NODE",
                    "labels_or_types": ["Herb"],
                    "properties": ["name"],
                }
            ],
        }
    )

    assert isinstance(response.indexes[0], GraphWorkbenchSchemaIndexItem)
    assert isinstance(response.constraints[0], GraphWorkbenchSchemaConstraintItem)
    assert response.indexes[0].labels_or_types == ["Herb"]
    assert response.constraints[0].properties == ["name"]
