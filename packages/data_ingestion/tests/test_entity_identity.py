from __future__ import annotations

from knowledge_model.constants import NodeType

from data_ingestion.entity_identity import (
    EntityDraft,
    IdentityError,
    assign_display_names,
    contains_brand,
    identity_key,
    merge_same_identity,
    redact_sensitive,
    sanitize_record,
    strip_latin_lines,
    strip_latin_properties,
)
from data_ingestion.dataset_records import DatasetRecord


def _draft(name: str, stable_id: str, *, parent: str = "", **props) -> EntityDraft:
    return EntityDraft(
        node_type=NodeType.DISEASE,
        raw_name=name,
        role="疾病",
        stable_id=stable_id,
        parent_name=parent,
        properties=props,
        evidence_refs=[stable_id],
    )


def test_same_code_merges_and_conflict_fails():
    merged, collapsed = merge_same_identity(
        [
            _draft("痞气", "12.4.13.1", description="小儿"),
            _draft("痞气", "12.4.13.1", description="小儿"),
        ]
    )
    assert collapsed == 1
    assert len(merged) == 1
    try:
        merge_same_identity(
            [
                _draft("痞气", "12.4.13.1", description="小儿"),
                _draft("痞气", "12.4.13.1", description="积聚"),
            ]
        )
    except IdentityError:
        return
    raise AssertionError("expected conflicting description")


def test_same_name_different_code_is_qualified():
    drafts = assign_display_names(
        [
            _draft("痞气", "12.4.13.1", parent="疳证"),
            _draft("痞气", "18.1.5", parent="积聚"),
        ]
    )
    names = {item.display_name for item in drafts}
    assert names == {"痞气（疳证）", "痞气（积聚）"}


def test_brand_and_pii_filters():
    assert contains_brand("同仁堂乌鸡白凤丸")
    assert not contains_brand("桂枝汤")
    text = redact_sensitive("电话13800138000 国药准字Z13022373 住院号123")
    assert "13800138000" not in text
    assert "Z13022373" not in text
    assert "123" not in text


def test_identity_key_keeps_same_name_different_ids_apart():
    left = identity_key("病证", "痞气", "12.4.13.1")
    right = identity_key("病证", "痞气", "18.1.5")
    assert left != right
    merged, collapsed = merge_same_identity(
        [
            _draft("痞气", "12.4.13.1"),
            _draft("痞气", "18.1.5"),
        ]
    )
    assert collapsed == 0
    assert len(merged) == 2


def test_strip_latin_names_aliases_and_evidence_lines():
    cleaned = strip_latin_properties(
        {
            "pinyin_name": "Renshen",
            "latin_name": "GINSENGRADIX",
            "拼音": "Renshen",
            "拉丁名": "GINSENGRADIX",
            "aliases": ["人参", "Panax ginseng", "ginseng"],
            "usage_text": "3～9g",
        }
    )
    assert cleaned == {"aliases": ["人参"], "usage_text": "3～9g"}
    evidence = "人参\nYizhihuanghua\nSOLIDAGINISHERBA\n本品为菊科植物。\nGINSENG RADIX"
    assert strip_latin_lines(evidence) == "人参\n本品为菊科植物。"
    record = sanitize_record(
        DatasetRecord(
            source_id="national-standard-2022-pharmacopoeia",
            batch_id="batch",
            unit_id="药材:人参",
            node_type="药材",
            node_name="人参",
            evidence_text=evidence,
            properties={"latin_name": "GINSENG", "aliases": ["人参", "Panax"]},
        )
    )
    assert "latin_name" not in record.properties
    assert record.properties["aliases"] == ["人参"]
    assert "Yizhihuanghua" not in (record.evidence_text or "")
    assert "本品为菊科植物。" in (record.evidence_text or "")
