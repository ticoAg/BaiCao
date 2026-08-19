from knowledge_model.graph_i18n import (
    PROPERTY_ZH_TO_EN,
    delocalize_status,
    localize_status,
    to_graph_properties,
    zh_property,
)


def test_property_and_status_are_chinese():
    assert zh_property("latin_name") == "拉丁名"
    assert localize_status("pending") == "待验证"
    assert delocalize_status("待验证") == "pending"
    assert delocalize_status("pending") == "pending"
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
    assert to_graph_properties({"snomed_id": "123456"})["SNOMED 标识"] == "123456"
    assert to_graph_properties({"cpm_id": "CPM00001"})["中成药标识"] == "CPM00001"
    assert to_graph_properties({"dosage_ratio": "0.5"})["剂量比例"] == "0.5"
    assert to_graph_properties({"storage_text": "置于燥处"})["贮藏"] == "置干燥处。"


def test_legacy_extract_keys_localize_and_unmapped_ascii_is_dropped():
    props = to_graph_properties(
        {
            "theory": "子午流注",
            "usage": "水煎服",
            "unknown_english_key": "should-drop",
            "名称": "保留中文键",
        }
    )
    assert props["理论"] == "子午流注"
    assert props["用法"] == "水煎服。"
    assert props["名称"] == "保留中文键"
    assert "unknown_english_key" not in props
    assert PROPERTY_ZH_TO_EN["用法"] == "usage_text"
