"""
BaiCao SSOT 枚举层
与 packages/shared/types/index.ts 完全对齐
所有枚举使用 StrEnum，确保与 string literal 完全兼容
"""

from enum import StrEnum

from graph_schema.constants import (
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
    HAS_PREPARED_FORM = "具有饮片"
    CONTAINS = "包含成分"
    EXTRACTED_FROM = "提取自"
    HAS_VARIANT = "具有品种"
    VARIANT_OF = "属于药材"
    PROCESSED_BY = "经过工艺"
    APPLIES_TO = "适用于"
    STORED_FOR = "储存时间"
    HAS_TRAIT = "具有性状"
    OBSERVED_IN = "观察于"
    HAS_EFFICACY = "具有功效"
    HAS_FLAVOR = "具有性味"
    ENTERS_MERIDIAN = "归于经脉"
    TREATS = "治疗病证"
    RELATED_HERB = "关联药材"
    RELATED_TREATMENT_METHOD = "关联治法"
    RELATED_SYNDROME = "关联证候"
    RELATED_SYMPTOM = "关联症状"
    INTERACTS_WITH = "相互作用"
    SIMILAR_TO = "相似于"
    PARENT_OF = "父类"
    CHILD_OF = "子类"
    ORIGINATED_FROM = "来源于"
    DERIVED_FROM = "派生自"
    SUPPORTED_BY = "由证据支持"
    CONTAINS_HERB = "组成药材"
    USES_FORMULA = "使用方剂"
    USES_ACUPOINT = "取用穴位"
    USES_METHOD = "采用治法"
    RECORDED_IN_CASE = "记载于医案"


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
