from data_ingestion.cli.merge_near_duplicates import plan_node_merges, plan_property_rewrites


def test_plan_rewrites_storage_punctuation_not_conditions():
    actions = plan_property_rewrites(
        [
            {"eid": "1", "key": "贮藏", "value": "置干燥处"},
            {"eid": "2", "key": "贮藏", "value": "置于燥处。"},
            {"eid": "3", "key": "贮藏", "value": "置阴凉干燥处，密闭保存，防蛀。"},
        ]
    )
    by_eid = {item["eid"]: item for item in actions}
    assert by_eid["1"]["to"] == "置干燥处。"
    assert by_eid["2"]["to"] == "置干燥处。"
    assert "3" not in by_eid


def test_plan_merges_flavor_ocr_into_existing():
    actions = plan_node_merges(
        [
            {"eid": "salty", "label": "性味", "name": "咸", "degree": 50, "props": {}},
            {"eid": "ocr", "label": "性味", "name": "成", "degree": 2, "props": {}},
            {"eid": "herb", "label": "药材", "name": "成", "degree": 1, "props": {}},
        ]
    )
    assert len(actions) == 1
    assert actions[0]["keep"] == "salty"
    assert actions[0]["canonical"] == "咸"
    assert actions[0]["drop"] == [{"eid": "ocr", "name": "成"}]


def test_plan_merges_disease_keeps_majority_form():
    actions = plan_node_merges(
        [
            {"eid": "a", "label": "病证", "name": "湿疹湿疮", "degree": 3, "props": {}},
            {"eid": "b", "label": "病证", "name": "湿疹、湿疮", "degree": 1, "props": {}},
        ]
    )
    assert actions[0]["keep"] == "a"
    assert actions[0]["canonical"] == "湿疹湿疮"
    assert actions[0]["drop"][0]["eid"] == "b"
