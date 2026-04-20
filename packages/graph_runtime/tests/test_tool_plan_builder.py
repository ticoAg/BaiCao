import graph_runtime.planner as planner
from graph_runtime.planner.plan_builder import build_graph_plan
from graph_runtime.planner.tool_plan_builder import build_initial_tool_plan


def test_tool_plan_builder_prefers_graph_cypher_for_abstract_query():
    plan = build_graph_plan("治感冒的中药都有哪些，怎么做")
    tool_plan = build_initial_tool_plan(plan)

    assert tool_plan[0].tool_name == "graph_cypher_qa"
    assert tool_plan[0].arguments["question"] == "治感冒的中药都有哪些，怎么做"


def test_tool_plan_builder_keeps_search_first_for_entity_query():
    plan = build_graph_plan("黄芩归什么经？")
    tool_plan = build_initial_tool_plan(plan)

    assert tool_plan[0].tool_name == "search_nodes"
    assert "query" in tool_plan[0].arguments
    assert tool_plan[0].arguments["query"]


def test_planner_public_exports_hide_unstable_planned_tool_call():
    assert "PlannedToolCall" not in planner.__all__
    assert "build_initial_tool_plan" in planner.__all__
