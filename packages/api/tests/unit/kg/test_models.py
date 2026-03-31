from app.kg.models import NODE_MODEL_MAP, REL_TYPE_TO_ATTR
from app.models.enums import EdgeType


def test_node_model_map_covers_runtime_labels() -> None:
    for label in [
        "Herb",
        "Component",
        "Variant",
        "Process",
        "Trait",
        "TimePoint",
        "Efficacy",
        "Flavor",
        "Meridian",
        "Disease",
        "Source",
        "Evidence",
    ]:
        assert label in NODE_MODEL_MAP


def test_rel_type_mapping_covers_runtime_links() -> None:
    assert REL_TYPE_TO_ATTR["具有功效"] == "has_efficacy"
    assert REL_TYPE_TO_ATTR["派生自"] == "derived_from"


def test_api_edge_type_keeps_api_only_superset_values() -> None:
    assert EdgeType.PARENT_OF.value == "父类"
    assert EdgeType.CHILD_OF.value == "子类"
