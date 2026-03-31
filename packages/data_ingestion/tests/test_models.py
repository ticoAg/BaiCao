from data_ingestion.models import ExtractionCandidate
from data_ingestion.source_models import RawEntryBlock, SourceFileContext
from knowledge_model.constants import NodeType


def test_extraction_candidate_targets_shared_node_type():
    candidate = ExtractionCandidate(
        node_type=NodeType.HERB,
        node_name="陈皮",
        source_name="中国药典",
    )

    assert candidate.node_type == NodeType.HERB


def test_data_ingestion_models_expose_field_descriptions_in_json_schema():
    candidate_schema = ExtractionCandidate.model_json_schema()

    assert candidate_schema["properties"]["node_type"]["description"] == "候选节点类型"
    assert candidate_schema["properties"]["source_name"]["description"] == "候选来源名称"
    assert candidate_schema["properties"]["properties"]["description"] == "候选节点属性集合"


def test_raw_entry_block_keeps_source_context():
    context = SourceFileContext(
        provider="huggingface",
        dataset="ZJUFanLab/TCMChat-dataset-600k",
        file_path="pretrain/train/books/national_standard/2022年中药药典.txt",
        local_abspath="/tmp/2022.txt",
        file_size=10,
        line_count=20,
    )
    block = RawEntryBlock(
        entry_id="entry-1",
        entry_title="一枝黄花",
        raw_text="一枝黄花\nYizhihuanghua",
        start_line=1,
        end_line=21,
        context=context,
    )

    assert block.context.dataset == "ZJUFanLab/TCMChat-dataset-600k"
    assert block.entry_title == "一枝黄花"
