from app.services.chat_agent_runtime.system_prompt import (
    build_graph_specialist_system_prompt,
    build_judge_instructions,
)


def test_system_prompt_requires_structured_tools_and_omits_raw_cypher():
    prompt = build_graph_specialist_system_prompt()
    assert "search_nodes" in prompt
    assert "search_edges" in prompt
    assert "expand_neighbors" in prompt
    assert "lookup_nodes" in prompt
    assert "read_cypher" not in prompt
    assert "不要编写或执行 Cypher" in prompt
    assert "不要编造" in prompt
    assert "Markdown" in prompt
    assert "不要输出思考过程" in prompt
    assert "没有图谱证据" in prompt
    assert "标识" in prompt
    assert "depth=2" in prompt
    assert "组成药材" not in prompt
    assert "使用方剂" not in prompt
    assert "judge" not in prompt


def test_judge_instructions_require_profiles_and_follow():
    text = build_judge_instructions()
    assert "profile=intake" in text
    assert "profile=evidence" in text
    assert "profile=claim" in text
    assert "follow" in text
    assert "不要自己编写选项或评分标准" in text
