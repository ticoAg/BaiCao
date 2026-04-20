from graph_runtime.planner.query_intent import classify_query_intent


def test_classify_query_intent_marks_symptom_question_as_abstract_graph_query():
    intent = classify_query_intent("治感冒的中药都有哪些，怎么做")

    assert intent.query_mode == "abstract_graph_query"
    assert "病证" in intent.target_node_types
    assert "治疗病证" in intent.target_edge_types


def test_classify_query_intent_marks_external_cold_question_as_abstract_graph_query():
    intent = classify_query_intent("外寒入里怎么办")

    assert intent.query_mode == "abstract_graph_query"
    assert intent.requires_cypher_agent is True


def test_classify_query_intent_keeps_entity_treatment_question_as_entity_lookup():
    intent = classify_query_intent("黄芩主治什么？")

    assert intent.query_mode == "entity_lookup"
    assert intent.requires_cypher_agent is False
