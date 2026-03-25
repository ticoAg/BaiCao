from data_ingestion.models import ExtractionCandidate
from knowledge_model.constants import NodeType


def test_extraction_candidate_targets_shared_node_type():
    candidate = ExtractionCandidate(
        node_type=NodeType.HERB,
        node_name="陈皮",
        source_name="中国药典",
    )

    assert candidate.node_type == NodeType.HERB
