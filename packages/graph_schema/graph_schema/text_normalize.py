"""图上近重复文本的通用归一。只合标点、空白、书名号和白名单 OCR，不合语义近义。"""

from __future__ import annotations

import re
import unicodedata
from collections import Counter, defaultdict
from typing import Iterable

SURFACE_PUNCT_RE = re.compile(
    r"[\s\u3000。．.，,、；;：:！!？?（）()【】\[\]“”\"'‘’《》〈〉·•\-—_~～]+"
)
WHITESPACE_RE = re.compile(r"[\s\u3000]+")
PHRASE_OCR = (
    ("置于燥", "置干燥"),
    ("置千燥", "置干燥"),
    ("置遁风", "置通风"),
    ("干燥赴", "干燥处"),
    ("鲜晶", "鲜品"),
)
LABEL_NAME_OCR: dict[str, dict[str, str]] = {
    "性味": {"成": "咸", "干": "甘", "淫": "涩"},
}
SENTENCE_KEYS = {
    "贮藏",
    "storage_text",
    "用法",
    "usage_text",
    "注意",
    "caution_text",
    "炮制方法",
    "processing_method_text",
    "说明",
    "description",
}
BOOK_KEYS = {"出处书名", "source_book"}
TERM_KEYS = {"主治", "indications"}
SHARED_MERGE_LABELS = {"功效", "性味", "归经", "病证", "治法", "穴位", "工艺"}


def apply_phrase_ocr(text: str) -> str:
    for old, new in PHRASE_OCR:
        text = text.replace(old, new)
    return text


def nfkc_strip(text: str) -> str:
    # NFC only: NFKC would fold （酒当归） into ASCII parentheses.
    return unicodedata.normalize("NFC", text).strip()


def surface_key(text: str) -> str:
    cleaned = apply_phrase_ocr(nfkc_strip(text)).replace("～", "~")
    return SURFACE_PUNCT_RE.sub("", cleaned)


def _prefer_cn_punct(text: str) -> str:
    return (
        text.replace(",", "，")
        .replace(";", "；")
        .replace(":", "：")
        .replace(".", "。")
        .replace("~", "～")
    )


def _score_variant(text: str, count: int, *, kind: str) -> tuple[int, int, int]:
    score = count * 10
    if kind == "book" and text.startswith("《") and text.endswith("》"):
        score += 20
    if kind == "sentence" and text.endswith("。"):
        score += 8
    if "，" in text:
        score += 2
    if any(old in text for old, _new in PHRASE_OCR):
        score -= 30
    return (score, len(text), -ord(text[0]) if text else 0)


def pick_canonical(variants: Iterable[str], *, kind: str = "sentence") -> str:
    cleaned: list[str] = []
    for item in variants:
        text = apply_phrase_ocr(nfkc_strip(str(item)))
        if kind == "book":
            title = text.strip("《》<>〈〉")
            text = f"《{title}》" if title else text
        elif kind == "sentence":
            text = _prefer_cn_punct(WHITESPACE_RE.sub("", text))
            if text and text[-1] not in "。！？":
                text = f"{text}。"
        elif kind == "term":
            text = _prefer_cn_punct(text).rstrip("。")
        else:
            text = _prefer_cn_punct(text)
        if text:
            cleaned.append(text)
    if not cleaned:
        return ""
    counts = Counter(cleaned)
    return max(counts, key=lambda item: _score_variant(item, counts[item], kind=kind))


def canonicalize_name(name: str, label: str | None = None) -> str:
    text = apply_phrase_ocr(nfkc_strip(name))
    if label and name in LABEL_NAME_OCR.get(label, {}):
        return LABEL_NAME_OCR[label][name]
    mapped = LABEL_NAME_OCR.get(label or "", {})
    return mapped.get(text, text)


def name_surface_key(name: str, label: str | None = None) -> str:
    return surface_key(canonicalize_name(name, label))


def property_kind(key: str) -> str | None:
    if key in SENTENCE_KEYS:
        return "sentence"
    if key in BOOK_KEYS:
        return "book"
    if key in TERM_KEYS:
        return "term"
    return None


def canonicalize_property_value(key: str, value: object) -> object:
    kind = property_kind(key)
    if kind is None:
        return value
    if isinstance(value, list):
        return [canonicalize_property_value(key, item) for item in value]
    if not isinstance(value, str) or not value.strip():
        return value
    return pick_canonical([value], kind=kind)


def group_variants(values: Iterable[str], *, kind: str) -> dict[str, str]:
    """surface_key -> canonical display form, only groups with 2+ raw variants."""
    buckets: dict[str, list[str]] = defaultdict(list)
    for raw in values:
        if raw is None or not str(raw).strip():
            continue
        buckets[surface_key(str(raw))].append(str(raw))
    mapping: dict[str, str] = {}
    for key, variants in buckets.items():
        if not key:
            continue
        canonical = pick_canonical(variants, kind=kind)
        for variant in set(variants):
            if variant != canonical:
                mapping[variant] = canonical
    return mapping
