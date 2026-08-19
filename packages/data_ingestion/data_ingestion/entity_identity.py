"""跨源共用的实体身份与合并门禁。

只允许同类型、同规范名、且稳定 ID 一致时合并。别名、拼音、编辑距离和
LLM 判断不参与身份。同名不同码必须保持独立，并给出可复现的限定名。
"""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Any

from knowledge_model.constants import NodeType
from knowledge_model.text_normalize import canonicalize_name

PHONE_RE = re.compile(r"(?<!\d)(?:1[3-9]\d{9}|0\d{2,3}-?\d{7,8})(?!\d)")
IDCARD_RE = re.compile(
    r"(?<!\d)[1-9]\d{5}(?:18|19|20)\d{2}(?:0[1-9]|1[0-2])(?:0[1-9]|[12]\d|3[01])\d{3}[\dXx](?!\d)"
)
ADMISSION_RE = re.compile(r"住院号[:：]?\s*\d+")
APPROVAL_RE = re.compile(r"国药准字[A-Za-z0-9]+")
BRAND_MARKERS = (
    "同仁堂",
    "云南白药",
    "片仔癀",
    "东阿阿胶",
    "哈药",
    "扬子江",
    "修正药业",
    "葵花药业",
    "999感冒",
)


class IdentityError(ValueError):
    pass


@dataclass
class EntityDraft:
    node_type: NodeType
    raw_name: str
    role: str
    stable_id: str
    aliases: list[str] = field(default_factory=list)
    properties: dict[str, Any] = field(default_factory=dict)
    evidence_refs: list[str] = field(default_factory=list)
    display_name: str = ""
    parent_name: str = ""
    edges: list[tuple[str, str]] = field(default_factory=list)


def name_key(name: str, node_type: NodeType | str | None = None) -> str:
    label = node_type.value if isinstance(node_type, NodeType) else node_type
    return canonicalize_name(name, label)


def contains_brand(text: str) -> bool:
    return any(marker in text for marker in BRAND_MARKERS)


def redact_sensitive(text: str) -> str:
    cleaned = PHONE_RE.sub("[已过滤电话]", text)
    cleaned = IDCARD_RE.sub("[已过滤证件]", cleaned)
    cleaned = ADMISSION_RE.sub("住院号[已过滤]", cleaned)
    cleaned = APPROVAL_RE.sub("[已过滤批准文号]", cleaned)
    return cleaned


def _qualify(draft: EntityDraft, siblings: list[EntityDraft]) -> str:
    parent = draft.parent_name.strip()
    parent_keys = {
        name_key(item.parent_name, item.node_type)
        for item in siblings
        if item.parent_name.strip()
    }
    if parent and len(parent_keys) == len(siblings):
        return f"{draft.raw_name}（{parent}）"
    return f"{draft.raw_name}〔{draft.stable_id}〕"


def assign_display_names(drafts: list[EntityDraft]) -> list[EntityDraft]:
    groups: dict[tuple[str, str], list[int]] = defaultdict(list)
    for index, draft in enumerate(drafts):
        key = (draft.node_type.value, name_key(draft.raw_name, draft.node_type))
        groups[key].append(index)
    for indexes in groups.values():
        if len(indexes) == 1:
            draft = drafts[indexes[0]]
            draft.display_name = draft.raw_name
            continue
        siblings = [drafts[index] for index in indexes]
        ids = {item.stable_id for item in siblings}
        if len(ids) == 1:
            for item in siblings:
                item.display_name = item.raw_name
            continue
        for item in siblings:
            item.display_name = _qualify(item, siblings)
    return drafts


def merge_same_identity(drafts: list[EntityDraft]) -> tuple[list[EntityDraft], int]:
    merged: dict[tuple[str, str, str], EntityDraft] = {}
    collapsed = 0
    for draft in drafts:
        key = (
            draft.node_type.value,
            name_key(draft.raw_name, draft.node_type),
            draft.stable_id,
        )
        existing = merged.get(key)
        if existing is None:
            merged[key] = draft
            continue
        collapsed += 1
        for alias in draft.aliases:
            if alias not in existing.aliases:
                existing.aliases.append(alias)
        for ref in draft.evidence_refs:
            if ref not in existing.evidence_refs:
                existing.evidence_refs.append(ref)
        for field_name, value in draft.properties.items():
            current = existing.properties.get(field_name)
            if current in (None, "", [], {}):
                existing.properties[field_name] = value
            elif value not in (None, "", [], {}) and current != value:
                raise IdentityError(
                    f"conflicting {field_name} for {draft.raw_name} {draft.stable_id}"
                )
        seen_edges = set(existing.edges)
        for edge in draft.edges:
            if edge not in seen_edges:
                existing.edges.append(edge)
                seen_edges.add(edge)
    return list(merged.values()), collapsed
