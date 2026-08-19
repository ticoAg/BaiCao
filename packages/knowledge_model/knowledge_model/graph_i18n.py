"""图谱存储用中文：标签、属性键、状态值、来源值。"""

from __future__ import annotations

from .constants import NodeType
from .text_normalize import canonicalize_property_value

LEGACY_NEO4J_LABELS: dict[NodeType, str] = {
    NodeType.HERB: "Herb",
    NodeType.PREPARED_HERB: "PreparedHerb",
    NodeType.COMPONENT: "Component",
    NodeType.VARIANT: "Variant",
    NodeType.PROCESS: "Process",
    NodeType.TRAIT: "Trait",
    NodeType.EFFICACY: "Efficacy",
    NodeType.FLAVOR: "Flavor",
    NodeType.MERIDIAN: "Meridian",
    NodeType.DISEASE: "Disease",
    NodeType.SYMPTOM: "Symptom",
    NodeType.FORMULA: "Formula",
    NodeType.MEDICAL_CASE: "MedicalCase",
    NodeType.ACUPOINT: "Acupoint",
    NodeType.TREATMENT_METHOD: "TreatmentMethod",
    NodeType.TIMEPOINT: "TimePoint",
    NodeType.SOURCE: "Source",
    NodeType.EVIDENCE: "Evidence",
}

PROPERTY_EN_TO_ZH: dict[str, str] = {
    "name": "名称",
    "id": "标识",
    "source": "来源",
    "status": "状态",
    "type": "类型",
    "category": "分类",
    "description": "说明",
    "latin_name": "拉丁名",
    "pinyin_name": "拼音",
    "base_description": "基原",
    "indications": "主治",
    "usage_text": "用法",
    "storage_text": "贮藏",
    "caution_text": "注意",
    "prepared_from_herb": "来自药材",
    "processing_method_text": "炮制方法",
    "raw_text": "原文",
    "evidence_text": "证据原文",
    "composition_text": "组成原文",
    "source_book": "出处书名",
    "chunk_hash": "文本块哈希",
    "dataset": "数据集",
    "dataset_name": "数据集名称",
    "source_provider": "来源提供方",
    "file_path": "文件路径",
    "entry_title": "条目标题",
    "evidence_id": "证据标识",
    "line_start": "起始行",
    "line_end": "结束行",
    "imported_at": "导入时间",
    "import_source_id": "导入源",
    "import_batch_id": "导入批次",
    "import_unit_id": "导入单元",
    "import_scope_key": "导入范围键",
    "import_source_ids": "导入源列表",
    "import_batch_ids": "导入批次列表",
    "import_scope_keys": "导入范围键列表",
    "prompt_hash": "抽取契约哈希",
    "prompt_hashes": "抽取契约哈希列表",
    "verification_id": "验证标识",
    "verified_by": "验证人",
    "verified_at": "验证时间",
    "chemical_formula": "化学式",
    "parent_herb": "所属药材",
    "min_duration": "最短时长",
    "conditions": "条件",
    "trait_category": "性状分类",
    "years": "年份",
    "quality_indicator": "质量指标",
    "nature": "药性",
    "tcm_type": "中医类型",
    "quantity": "用量",
    "toxicity": "毒性",
    "dosage": "剂量",
    "observation": "观察",
    "value": "取值",
    "duration": "时长",
    "alias": "别名",
    "skip_reason": "跳过原因",
    "aliases": "别名列表",
    "formula_count": "方剂数量",
    "acupoints": "穴位列表",
    "ratio_note": "配比说明",
    "ratio_range": "配比范围",
    "from_daoyi_suyang": "来自道医苏子阳",
    "formula_name": "方剂名",
    "symptoms": "症状",
    "usage": "用法",
    "method": "方法",
    "form": "剂型",
    "practice_times": "练习次数",
    "theory": "理论",
    "tongue": "舌象",
    "number_theory": "数理",
    "patient_context": "患者背景",
    "formula_context": "方剂背景",
    "principle": "治则",
    "pulse": "脉象",
    "course": "病程",
    "origin": "产地",
    "real_use": "实际用法",
    "precautions": "注意事项",
    "patient": "患者",
    "cause": "病因",
    "author": "作者",
    "context": "背景",
    "water_level": "水位",
    "interval": "间隔",
    "symptom": "症状",
    "pulse_change": "脉象变化",
    "dose": "剂量",
    "speaker": "讲述人",
    "meridian": "经脉",
    "location": "部位",
    "indication": "适应证",
    "note": "备注",
    "etiology": "病因",
    "therapy": "疗法",
    "cited_in": "引用处",
    "used_in": "用于",
    "components": "成分列表",
    "herb": "药材",
    "component_of": "所属成分",
    "preparation": "炮制",
    "topic": "主题",
    "start_date": "开始日期",
    "end_date": "结束日期",
    "year_range": "年份范围",
    "bencao_raw": "本草原文",
    "chapter": "篇章",
    "commentary": "讲解",
    "contraindication": "禁忌",
    "core_symptoms": "核心症状",
    "course_ref": "课程引用",
    "differential": "鉴别说明",
    "differentiation": "辨证说明",
    "eight_principles": "八纲",
    "evidence_ref": "证据定位",
    "first_gateway": "首问入口",
    "flavor_text": "性味原文",
    "is_high_risk": "高风险",
    "key_differentiation": "鉴别要点",
    "lesson_ref": "课次引用",
    "meridian_tropism": "归经原文",
    "raw_path": "原始路径",
    "related_acupoints": "相关穴位原文",
    "related_herbs": "相关药材原文",
    "related_pathomechanism": "相关病机原文",
    "representative_formulas": "代表方原文",
    "required_questions": "必问问题",
    "six_channel": "六经",
    "source_repo": "来源仓库",
    "syndrome_text": "证候原文",
    "target_module": "目标模块",
}

PROPERTY_ZH_TO_EN: dict[str, str] = {}
for _en, _zh in PROPERTY_EN_TO_ZH.items():
    PROPERTY_ZH_TO_EN.setdefault(_zh, _en)

STATUS_EN_TO_ZH: dict[str, str] = {
    "pending": "待验证",
    "verified": "已验证",
    "rejected": "已拒绝",
}
STATUS_ZH_TO_EN: dict[str, str] = {zh: en for en, zh in STATUS_EN_TO_ZH.items()}

SOURCE_VALUE_EN_TO_ZH: dict[str, str] = {
    "huggingface": "2022年中药药典",
    "daoyi-suyang": "道医苏子阳",
    "national-standard-2022-pharmacopoeia": "2022年中药药典",
}

SCOPE_VALUE_EN_TO_ZH: dict[str, str] = {
    "manual:baicao-knowledge:daoyi-suyang": "人工:白草知识:道医苏子阳",
    "huggingface|ZJUFanLab/TCMChat-dataset-600k|pretrain/train/books/national_standard/2022年中药药典.txt": "抱抱脸:中药药典2022",
    "huggingface:ZJUFanLab/TCMChat-dataset-600k:pretrain/train/books/national_standard/2022年中药药典.txt": "抱抱脸:中药药典2022",
}

PROVIDER_VALUE_EN_TO_ZH: dict[str, str] = {
    "huggingface": "抱抱脸",
    "manual": "人工",
}


def is_ascii_property_key(key: str) -> bool:
    return bool(key) and all(ord(char) < 128 for char in key)


def zh_property(key: str) -> str:
    return PROPERTY_EN_TO_ZH.get(key, key)


def localize_status(value: str | None) -> str | None:
    if value is None:
        return None
    return STATUS_EN_TO_ZH.get(value, value)


def delocalize_status(value: str | None) -> str | None:
    if value is None:
        return None
    return STATUS_ZH_TO_EN.get(value, value)


def localize_value(key: str, value: object) -> object:
    if not isinstance(value, str):
        if isinstance(value, list):
            return [localize_value(key, item) for item in value]
        return value
    if key in {"status", "状态"}:
        return STATUS_EN_TO_ZH.get(value, value)
    if key in {"source", "来源", "import_source_id", "导入源"}:
        return SOURCE_VALUE_EN_TO_ZH.get(value, value)
    if key in {"import_scope_key", "导入范围键"}:
        return SCOPE_VALUE_EN_TO_ZH.get(value, value)
    if key in {"source_provider", "来源提供方"}:
        return PROVIDER_VALUE_EN_TO_ZH.get(value, value)
    return value


def to_graph_properties(props: dict[str, object]) -> dict[str, object]:
    localized: dict[str, object] = {}
    for key, value in props.items():
        if value is None:
            continue
        chinese_key = zh_property(key)
        if chinese_key == key and is_ascii_property_key(key):
            continue
        localized[chinese_key] = canonicalize_property_value(chinese_key, localize_value(key, value))
    return localized
