from app.services.chat_agent_runtime.system_prompt import build_graph_specialist_system_prompt


def test_system_prompt_requires_chinese_keys_and_tool_order():
    prompt = build_graph_specialist_system_prompt()
    assert "search_nodes" in prompt
    assert "expand_neighbors" in prompt
    assert "n.标识" in prompt
    assert "n.name" in prompt
    assert "组成药材" in prompt
    assert "不要编造" in prompt
    assert "Markdown" in prompt
    assert "不要输出思考过程" in prompt
