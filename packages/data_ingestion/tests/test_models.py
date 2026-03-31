from data_ingestion.models import ExtractionCandidate
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
