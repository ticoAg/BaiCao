import pytest

pytestmark = pytest.mark.contract


def test_api_schemas_expose_field_descriptions_in_json_schema():
    from app.export.schemas import ExportPlanResponse
    from app.pipeline.materialization import MaterializedSource
    from app.pipeline.schemas import PipelineStepPreviewResponse
    from app.review.schemas import ReviewSessionResponse
    from app.schemas.graph import GraphQueryRequest
    from app.schemas.graph_workbench import GraphWorkbenchMetaSummary
    from app.schemas.user import UserRead
    from app.schemas.workbench import CypherValidationRequest

    graph_query_schema = GraphQueryRequest.model_json_schema()
    materialized_source_schema = MaterializedSource.model_json_schema()
    pipeline_preview_schema = PipelineStepPreviewResponse.model_json_schema()
    export_plan_schema = ExportPlanResponse.model_json_schema()
    review_session_schema = ReviewSessionResponse.model_json_schema()
    workbench_summary_schema = GraphWorkbenchMetaSummary.model_json_schema()
    cypher_validation_schema = CypherValidationRequest.model_json_schema()
    user_read_schema = UserRead.model_json_schema()

    assert graph_query_schema["properties"]["depth"]["description"] == "图查询展开深度"
    assert materialized_source_schema["properties"]["candidate_files"]["description"] == "候选数据文件列表"
    assert pipeline_preview_schema["properties"]["artifacts"]["description"] == "关联产物列表"
    assert export_plan_schema["properties"]["blocking_issues"]["description"] == "阻塞导出的检查问题列表"
    assert review_session_schema["properties"]["items"]["description"] == "当前评审会话中的条目列表"
    assert workbench_summary_schema["properties"]["node_count"]["description"] == "图数据库节点总数"
    assert cypher_validation_schema["properties"]["query"]["description"] == "待校验的 Cypher 语句"
    assert user_read_schema["properties"]["expert_fields"]["description"] == "专家领域列表"
