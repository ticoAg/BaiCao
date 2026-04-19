"""覆盖药典 LLM 抽取 prompt 与结果模型契约。"""

from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.extraction_models import (
    PharmacopoeiaEntrySections,
    PharmacopoeiaExtractionResult,
)
from data_ingestion.processors.huggingface.zjufanlab_tcmchat_dataset_600k.national_standard_2022_pharmacopoeia.prompts import (
    PHARMACOPOEIA_EXTRACTION_SYSTEM_PROMPT,
    build_pharmacopoeia_user_payload,
)


def test_prompt_payload_uses_single_evidence_block_only():
    """验证当前 prompt payload 只暴露单个证据块原文。"""

    sections = PharmacopoeiaEntrySections(
        title_zh="一枝黄花",
        header_lines=["Yizhihuanghua", "SOLIDAGINISHERBA"],
        base_description="本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。",
        sections={"性状": "本品长30～100cm。"},
        piece_sections={"性味与归经": "辛、苦，凉。归肺、肝经。"},
        raw_text="一枝黄花\nYizhihuanghua\nSOLIDAGINISHERBA\n本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。\n饮片\n【性味与归经】辛、苦，凉。归肺、肝经。",
    )

    payload = build_pharmacopoeia_user_payload(sections)

    assert payload["entry_title"] == "一枝黄花"
    assert payload["evidence_text"].startswith("一枝黄花\nYizhihuanghua")
    assert "piece_sections" not in payload
    assert "sections" not in payload
    assert "raw_text" not in payload


def test_extraction_result_accepts_piece_usage_storage_and_notes():
    """验证扩展后的饮片字段可以通过结果模型校验。"""

    result = PharmacopoeiaExtractionResult.model_validate(
        {
            "herb": {
                "herb_name": "一枝黄花",
                "pinyin_name": "Yizhihuanghua",
                "latin_name": "SOLIDAGINISHERBA",
                "base_description": "本品为菊科植物一枝黄花SolidagodecurrensLour.的干燥全草。",
            },
            "prepared_piece": {
                "piece_name": "一枝黄花饮片",
                "parent_herb_name": "一枝黄花",
                "processing_text": "除去杂质，喷淋清水，切段，干燥。",
                "flavors": ["辛", "苦"],
                "nature": "凉",
                "meridians": ["肺经", "肝经"],
                "efficacies": ["清热解毒", "疏散风热"],
                "indications": ["喉痹", "风热感冒"],
                "usage_text": "9～15g。",
                "storage_text": "置干燥处。",
                "caution_text": None,
            },
            "warnings": [],
            "confidence_notes": "饮片 section 信息完整。",
        }
    )

    assert result.prepared_piece is not None
    assert result.prepared_piece.usage_text == "9～15g。"


def test_extraction_result_normalizes_singleton_prepared_piece_list():
    """验证 LLM 偶发返回单元素饮片列表时会在边界归一化。"""

    result = PharmacopoeiaExtractionResult.model_validate(
        {
            "herb": {"herb_name": "牛蒡子"},
            "prepared_piece": [
                {
                    "piece_name": "牛蒡子",
                    "parent_herb_name": "牛蒡子",
                    "processing_text": "除去杂质，洗净，干燥。",
                }
            ],
        }
    )

    assert result.prepared_piece is not None
    assert result.prepared_piece.piece_name == "牛蒡子"


def test_extraction_result_fills_missing_piece_name_from_parent_herb_name():
    """验证饮片名为空时会回退到父级药材名。"""

    result = PharmacopoeiaExtractionResult.model_validate(
        {
            "herb": {"herb_name": "两面针"},
            "prepared_piece": {
                "piece_name": None,
                "parent_herb_name": "两面针",
                "processing_text": "除去杂质，洗净，切片，干燥。",
            },
        }
    )

    assert result.prepared_piece is not None
    assert result.prepared_piece.piece_name == "两面针"


def test_extraction_result_normalizes_null_piece_lists_to_empty_lists():
    """验证饮片列表字段为 null 时会归一化为空数组。"""

    result = PharmacopoeiaExtractionResult.model_validate(
        {
            "herb": {"herb_name": "棕榈"},
            "prepared_piece": {
                "piece_name": "棕榈",
                "parent_herb_name": "棕榈",
                "flavors": None,
                "meridians": None,
                "efficacies": None,
                "indications": None,
            },
        }
    )

    assert result.prepared_piece is not None
    assert result.prepared_piece.flavors == []
    assert result.prepared_piece.meridians == []
    assert result.prepared_piece.efficacies == []
    assert result.prepared_piece.indications == []


def test_system_prompt_mentions_json_for_structured_output():
    """验证系统提示词明确要求返回 JSON。"""

    assert "json" in PHARMACOPOEIA_EXTRACTION_SYSTEM_PROMPT.lower()


def test_system_prompt_contains_schema_example_and_field_guidance():
    """验证系统提示词包含字段示例和输出约束。"""

    assert '"herb"' in PHARMACOPOEIA_EXTRACTION_SYSTEM_PROMPT
    assert '"prepared_piece"' in PHARMACOPOEIA_EXTRACTION_SYSTEM_PROMPT
    assert "必须严格使用以下字段名" in PHARMACOPOEIA_EXTRACTION_SYSTEM_PROMPT
