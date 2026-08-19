from app.services.chat_agent_runtime.citations import citations_from_graph_state


def _graph_state(*, nodes: list[dict], edges: list[dict]) -> dict:
    return {
        "nodes": {str(node.get("id") or node.get("name")): node for node in nodes},
        "edges": {str(index): edge for index, edge in enumerate(edges)},
        "center_node_id": None,
        "actual_depth": 0,
    }


def test_citations_from_supported_by_and_originated_from_edges():
    citations = citations_from_graph_state(
        _graph_state(
            nodes=[
                {"id": "药材:乌梅", "name": "乌梅", "labels": ["药材"]},
                {
                    "id": "证据:suyang-002",
                    "name": "证据:suyang-002",
                    "labels": ["证据"],
                    "evidence_text": "乌梅味酸，能涩肠止痢。",
                },
                {"id": "来源:道医苏子阳", "name": "道医苏子阳", "labels": ["来源"]},
            ],
            edges=[
                {
                    "rel_type": "由证据支持",
                    "source": {"id": "药材:乌梅"},
                    "target": {"id": "证据:suyang-002"},
                },
                {
                    "rel_type": "来源于",
                    "source": {"id": "证据:suyang-002"},
                    "target": {"id": "来源:道医苏子阳"},
                },
            ],
        )
    )

    assert citations == [
        {
            "entity_id": "药材:乌梅",
            "evidence_id": "证据:suyang-002",
            "snippet": "乌梅味酸，能涩肠止痢。",
            "source_id": "来源:道医苏子阳",
            "source_name": "道医苏子阳",
        }
    ]


def test_citations_attach_source_from_entity_originated_from_edge():
    citations = citations_from_graph_state(
        _graph_state(
            nodes=[
                {"id": "药材:乌梅", "name": "乌梅", "labels": ["药材"]},
                {
                    "id": "证据:suyang-002",
                    "name": "证据:suyang-002",
                    "labels": ["证据"],
                    "evidence_text": "乌梅味酸，能涩肠止痢。",
                },
                {"id": "来源:道医苏子阳", "name": "道医苏子阳", "labels": ["来源"]},
            ],
            edges=[
                {
                    "rel_type": "由证据支持",
                    "source": {"id": "药材:乌梅"},
                    "target": {"id": "证据:suyang-002"},
                },
                {
                    "rel_type": "来源于",
                    "source": {"id": "药材:乌梅"},
                    "target": {"id": "来源:道医苏子阳"},
                },
            ],
        )
    )

    assert citations == [
        {
            "entity_id": "药材:乌梅",
            "evidence_id": "证据:suyang-002",
            "snippet": "乌梅味酸，能涩肠止痢。",
            "source_id": "来源:道医苏子阳",
            "source_name": "道医苏子阳",
        }
    ]


def test_citations_prefer_entity_source_over_legacy_evidence_source():
    citations = citations_from_graph_state(
        _graph_state(
            nodes=[
                {"id": "药材:乌梅", "name": "乌梅", "labels": ["药材"]},
                {
                    "id": "证据:suyang-002",
                    "name": "证据:suyang-002",
                    "labels": ["证据"],
                    "evidence_text": "乌梅味酸，能涩肠止痢。",
                },
                {"id": "来源:主来源", "name": "主来源", "labels": ["来源"]},
                {"id": "来源:兼容来源", "name": "兼容来源", "labels": ["来源"]},
            ],
            edges=[
                {
                    "rel_type": "由证据支持",
                    "source": "药材:乌梅",
                    "target": "证据:suyang-002",
                },
                {
                    "rel_type": "来源于",
                    "source": "药材:乌梅",
                    "target": "来源:主来源",
                },
                {
                    "rel_type": "来源于",
                    "source": "证据:suyang-002",
                    "target": "来源:兼容来源",
                },
            ],
        )
    )

    assert citations[0]["source_id"] == "来源:主来源"
    assert citations[0]["source_name"] == "主来源"


def test_citations_omit_source_when_originated_from_missing():
    citations = citations_from_graph_state(
        _graph_state(
            nodes=[
                {"id": "方剂:乌梅丸", "name": "乌梅丸", "labels": ["方剂"]},
                {
                    "id": "证据:only",
                    "name": "证据:only",
                    "labels": ["证据"],
                    "evidence_text": "乌梅丸治久利。",
                },
            ],
            edges=[
                {
                    "type": "由证据支持",
                    "source": "方剂:乌梅丸",
                    "target": "证据:only",
                }
            ],
        )
    )

    assert citations == [
        {
            "entity_id": "方剂:乌梅丸",
            "evidence_id": "证据:only",
            "snippet": "乌梅丸治久利。",
        }
    ]


def test_citations_ignore_unrelated_nodes_edges_and_disconnected_evidence():
    citations = citations_from_graph_state(
        _graph_state(
            nodes=[
                {"id": "药材:桂枝", "name": "桂枝", "labels": ["药材"]},
                {"id": "功效:解表", "name": "解表", "labels": ["功效"]},
                {
                    "id": "证据:orphan",
                    "name": "证据:orphan",
                    "labels": ["证据"],
                    "evidence_text": "这是一条没有由证据支持边的摘录。",
                },
                {"id": "来源:药典", "name": "中国药典", "labels": ["来源"]},
            ],
            edges=[
                {
                    "rel_type": "具有功效",
                    "source": {"id": "药材:桂枝"},
                    "target": {"id": "功效:解表"},
                },
                {
                    "rel_type": "来源于",
                    "source": {"id": "证据:orphan"},
                    "target": {"id": "来源:药典"},
                },
            ],
        )
    )

    assert citations == []


def test_citations_skip_dangling_or_unidentified_nodes():
    citations = citations_from_graph_state(
        _graph_state(
            nodes=[
                {"id": "药材:甘草", "name": "甘草", "labels": ["药材"]},
                {
                    "name": "无标识证据",
                    "labels": ["证据"],
                    "evidence_text": "没有标识，不应生成引用。",
                },
                {
                    "id": "证据:no-label",
                    "name": "证据:no-label",
                    "evidence_text": "没有证据标签，不应生成引用。",
                },
                {
                    "id": "证据:ok",
                    "name": "证据:ok",
                    "labels": ["证据"],
                    "evidence_text": "甘草甘平。",
                },
            ],
            edges=[
                {
                    "rel_type": "由证据支持",
                    "source": {"id": "药材:甘草"},
                    "target": {"id": "证据:missing"},
                },
                {
                    "rel_type": "由证据支持",
                    "source": {"id": "药材:甘草"},
                    "target": {"name": "无标识证据"},
                },
                {
                    "rel_type": "由证据支持",
                    "source": {"id": "药材:甘草"},
                    "target": {"id": "证据:no-label"},
                },
                {
                    "rel_type": "由证据支持",
                    "source": {"id": "药材:甘草"},
                    "target": {"id": "证据:ok"},
                },
            ],
        )
    )

    assert citations == [
        {
            "entity_id": "药材:甘草",
            "evidence_id": "证据:ok",
            "snippet": "甘草甘平。",
        }
    ]


def test_citations_dedupe_stably_and_read_chinese_property_keys():
    citations = citations_from_graph_state(
        {
            "nodes": {
                "药材:黄连": {"id": "药材:黄连", "name": "黄连", "labels": ["药材"]},
                "药材:黄芩": {"id": "药材:黄芩", "name": "黄芩", "labels": ["药材"]},
                "证据:b": {
                    "标识": "证据:b",
                    "名称": "证据:b",
                    "labels": ["证据"],
                    "证据原文": "黄芩苦寒。",
                },
                "证据:a": {
                    "id": "证据:a",
                    "name": "证据:a",
                    "labels": ["Evidence"],
                    "raw_text": "黄连苦寒。",
                },
            },
            "edges": {
                "later": {
                    "rel_type": "由证据支持",
                    "source": {"id": "药材:黄芩"},
                    "target": {"id": "证据:b"},
                },
                "dup-1": {
                    "rel_type": "由证据支持",
                    "source": {"id": "药材:黄连"},
                    "target": {"id": "证据:a"},
                },
                "dup-2": {
                    "type": "由证据支持",
                    "source": "药材:黄连",
                    "target": "证据:a",
                },
            },
        }
    )

    assert [item["evidence_id"] for item in citations] == ["证据:a", "证据:b"]
    assert citations[0]["entity_id"] == "药材:黄连"
    assert citations[0]["snippet"] == "黄连苦寒。"
    assert citations[1]["snippet"] == "黄芩苦寒。"
    assert len(citations) == 2
