from app.kg.models import NODE_MODEL_MAP, REL_TYPE_TO_ATTR


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
    assert REL_TYPE_TO_ATTR["HAS_EFFICACY"] == "has_efficacy"
    assert REL_TYPE_TO_ATTR["DERIVED_FROM"] == "derived_from"
