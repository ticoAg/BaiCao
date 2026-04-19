"""提供药典抽取中常见性味和归经字段的轻量归一化函数。"""

import re


_KNOWN_FLAVORS = {"辛", "甘", "苦", "酸", "咸", "淡", "涩"}
_KNOWN_NATURES = {"寒", "热", "温", "凉", "平", "微寒", "微温"}


def normalize_flavors_and_nature(text: str) -> tuple[list[str], str | None]:
    """从“性味与归经”文本里拆出性味列表和药性。"""

    parts = [part.strip() for part in re.split(r"[、，,]", text.split("。", 1)[0]) if part.strip()]
    flavors = [part for part in parts if part in _KNOWN_FLAVORS]
    nature = next((part for part in parts if part in _KNOWN_NATURES), None)
    return flavors, nature


def normalize_meridians(text: str) -> list[str]:
    """从“归某经”样式文本里归一出带“经”后缀的归经列表。"""

    if "归" in text:
        text = text.split("归", 1)[1]
    items = [item.strip() for item in re.split(r"[、，,]", text.replace("。", "")) if item.strip()]
    return [item if item.endswith("经") else f"{item}经" for item in items]
