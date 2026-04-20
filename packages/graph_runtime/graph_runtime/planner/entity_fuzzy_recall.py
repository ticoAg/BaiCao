QUESTION_PUNCTUATION = "？?！!，,。.:：；;、"
REMOVABLE_PHRASES = [
    "请告诉我",
    "告诉我",
    "给我",
    "帮我",
    "请问",
    "一下",
    "可以",
    "什么",
    "哪些",
    "归什么经",
    "走什么经",
    "归经",
    "功效",
    "主治",
    "作用",
    "原文证据",
    "原文",
    "证据",
    "出处",
]


def normalize_question(question: str) -> str:
    normalized = question
    for token in QUESTION_PUNCTUATION:
        normalized = normalized.replace(token, " ")
    return " ".join(normalized.split())


def recall_entity_keywords(question: str) -> list[str]:
    normalized = normalize_question(question)
    if not normalized:
        return []

    candidates: list[str] = []
    stripped = normalized
    for phrase in sorted(REMOVABLE_PHRASES, key=len, reverse=True):
        stripped = stripped.replace(phrase, " ")
    collapsed = "".join(stripped.split())
    if collapsed:
        candidates.append(collapsed)
    if normalized:
        candidates.append(normalized)
    return list(dict.fromkeys(candidate for candidate in candidates if candidate))
