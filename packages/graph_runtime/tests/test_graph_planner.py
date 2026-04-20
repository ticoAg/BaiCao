from graph_runtime.planner.plan_builder import build_graph_plan


def test_plan_builder_maps_meridian_question_to_schema_targets():
    plan = build_graph_plan("黄芩归什么经？")

    assert "归经" in plan["target_node_types"]
    assert "归于经脉" in plan["target_edge_types"]


def test_plan_builder_maps_evidence_question_to_supported_by():
    plan = build_graph_plan("给我黄芩的原文证据")

    assert "证据" in plan["target_node_types"]
    assert "由证据支持" in plan["target_edge_types"]
