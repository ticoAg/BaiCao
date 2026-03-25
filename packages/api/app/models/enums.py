"""
BaiCao SSOT 枚举层
与 packages/shared/types/index.ts 完全对齐
所有枚举使用 StrEnum，确保与 string literal 完全兼容
"""

from enum import StrEnum

from knowledge_model.constants import (
    HerbType,
    NodeStatus,
    NodeType,
    TraitCategory,
)


# ============ User & Auth ============

class UserRole(StrEnum):
    USER = "user"
    EXPERT = "expert"
    ADMIN = "admin"


# ============ Source ============

class SourceType(StrEnum):
    ANCIENT = "ancient"
    MODERN = "modern"
    PATENT = "patent"
    DATABASE = "database"


# ============ Verification ============

class VerificationStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class EntityType(StrEnum):
    HERB = "herb"
    COMPONENT = "component"
    VARIANT = "variant"
    PROCESS = "process"
    TRAIT = "trait"
    EFFICACY = "efficacy"
    RELATION = "relation"


# ============ Graph Edge Types ============

class EdgeType(StrEnum):
    CONTAINS = "CONTAINS"
    EXTRACTED_FROM = "EXTRACTED_FROM"
    HAS_VARIANT = "HAS_VARIANT"
    VARIANT_OF = "VARIANT_OF"
    PROCESSED_BY = "PROCESSED_BY"
    APPLIES_TO = "APPLIES_TO"
    STORED_FOR = "STORED_FOR"
    HAS_TRAIT = "HAS_TRAIT"
    OBSERVED_IN = "OBSERVED_IN"
    HAS_EFFICACY = "HAS_EFFICACY"
    HAS_FLAVOR = "HAS_FLAVOR"
    ENTERS_MERIDIAN = "ENTERS_MERIDIAN"
    TREATS = "TREATS"
    INTERACTS_WITH = "INTERACTS_WITH"
    SIMILAR_TO = "SIMILAR_TO"
    PARENT_OF = "PARENT_OF"
    CHILD_OF = "CHILD_OF"
    ORIGINATED_FROM = "ORIGINATED_FROM"


# ============ Chat ============

class MessageRole(StrEnum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


__all__ = [
    "UserRole",
    "SourceType",
    "VerificationStatus",
    "EntityType",
    "NodeType",
    "NodeStatus",
    "EdgeType",
    "HerbType",
    "TraitCategory",
    "MessageRole",
]
