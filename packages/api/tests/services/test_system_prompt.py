from app.services.chat_agent_runtime.system_prompt import build_graph_specialist_system_prompt


def test_system_prompt_requires_structured_tools_and_omits_raw_cypher():
    prompt = build_graph_specialist_system_prompt()
    assert "search_nodes" in prompt
    assert "search_edges" in prompt
    assert "expand_neighbors" in prompt
    assert "lookup_nodes" in prompt
    assert "read_cypher" not in prompt
    assert "不要编写或执行 Cypher" in prompt
    assert "组成药材" in prompt
    assert "不要编造" in prompt
    assert "Markdown" in prompt
    assert "不要输出思考过程" in prompt
    assert "由证据支持" in prompt
    assert "来源于" in prompt
    assert "证据" in prompt
    assert "来源" in prompt
    assert "没有图谱证据" in prompt
