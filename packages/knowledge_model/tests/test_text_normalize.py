from knowledge_model.text_normalize import (
    canonicalize_name,
    canonicalize_property_value,
    group_variants,
    pick_canonical,
    surface_key,
)


def test_storage_ocr_and_punctuation_collapse():
    assert surface_key("置于燥处。") == surface_key("置干燥处")
    assert surface_key("置千燥处。") == "置干燥处"
    assert surface_key("置遁风干燥处，防霉，防蛀。") == surface_key("置通风干燥处，防霉、防蛀。")
    assert pick_canonical(["置干燥处", "置于燥处。", "置千燥处。"], kind="sentence") == "置干燥处。"


def test_does_not_merge_different_storage_conditions():
    assert surface_key("置干燥处。") != surface_key("置阴凉干燥处，密闭保存，防蛀。")
    mapping = group_variants(
        ["置干燥处。", "置阴凉干燥处。", "置干燥处"],
        kind="sentence",
    )
    assert mapping["置干燥处"] == "置干燥处。"
    assert "置阴凉干燥处。" not in mapping


def test_usage_and_caution_period_only():
    assert pick_canonical(["9～15g", "9～15g。"], kind="sentence") == "9～15g。"
    assert pick_canonical(["孕妇慎用", "孕妇慎用。"], kind="sentence") == "孕妇慎用。"


def test_book_title_marks():
    assert pick_canonical(["金匮要略", "《金匮要略》"], kind="book") == "《金匮要略》"
    assert canonicalize_property_value("出处书名", "辨证录") == "《辨证录》"


def test_fullwidth_parens_stay_chinese():
    assert pick_canonical(["活血通经（酒当归）"], kind="term") == "活血通经（酒当归）"


def test_flavor_ocr_names():
    assert canonicalize_name("成", "性味") == "咸"
    assert canonicalize_name("干", "性味") == "甘"
    assert canonicalize_name("淫", "性味") == "涩"
    assert canonicalize_name("干", "药材") == "干"


def test_disease_term_variants():
    mapping = group_variants(["湿疹湿疮", "湿疹湿疮", "湿疹湿疮", "湿疹、湿疮"], kind="term")
    assert mapping["湿疹、湿疮"] == "湿疹湿疮"
    assert surface_key("湿疹、湿疮") == surface_key("湿疹湿疮")
