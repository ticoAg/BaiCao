from knowledge_model.graph_i18n import localize_status, to_graph_properties, zh_property


def test_property_and_status_are_chinese():
    assert zh_property("latin_name") == "拉丁名"
    assert localize_status("pending") == "待验证"
    props = to_graph_properties(
        {
            "name": "人参",
            "source": "huggingface",
            "status": "pending",
            "import_source_id": "daoyi-suyang",
            "import_scope_key": "manual:baicao-knowledge:daoyi-suyang",
        }
    )
    assert props["名称"] == "人参"
    assert props["来源"] == "2022年中药药典"
    assert props["状态"] == "待验证"
    assert props["导入源"] == "道医苏子阳"
    assert props["导入范围键"] == "人工:白草知识:道医苏子阳"
