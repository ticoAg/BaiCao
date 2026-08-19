from __future__ import annotations

from knowledge_model.constants import NodeType

from data_ingestion.entity_identity import (
    EntityDraft,
    IdentityError,
    assign_display_names,
    contains_brand,
    merge_same_identity,
    redact_sensitive,
)


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
