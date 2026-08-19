from fastapi import APIRouter, HTTPException

from ..provenance import provenance_service
from ..schemas.provenance import (
    CreateEvidenceRequest,
    EvidenceCollectionResponse,
    EvidenceResponse,
    LineageChainResponse,
    LineageCompletenessResponse,
    LinkSourceRequest,
    LinkSourceResponse,
    SourceDerivationsResponse,
)

router = APIRouter(prefix="/provenance", tags=["provenance"])


@router.post("/evidence", response_model=EvidenceResponse)
async def create_evidence(request: CreateEvidenceRequest):
    """创建证据节点"""
    return await provenance_service.create_evidence(
        content=request.content,
        source_name=request.source_name,
        page_reference=request.page_reference,
    )


@router.get("/evidence/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(evidence_id: str):
    """获取证据详情"""
    result = await provenance_service.get_evidence(evidence_id)
    if not result:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return result


@router.post("/evidence/{evidence_id}/link-source", response_model=LinkSourceResponse)
async def link_evidence_to_source(evidence_id: str, request: LinkSourceRequest):
    """关联证据与来源 (来源于 关系)"""
    result = await provenance_service.link_evidence_to_source(
        evidence_id=evidence_id,
        source_id=request.source_id,
    )
    if not result:
        raise HTTPException(status_code=404, detail="Evidence or source not found")
    return {"relationship": result, "message": "Evidence linked to source"}


@router.get("/entity/{entity_id}/lineage", response_model=LineageChainResponse)
async def get_entity_lineage(entity_id: str):
    """查询实体溯源链: Entity -[:由证据支持]-> 证据，优先 Entity -[:来源于]-> 来源"""
    lineage = await provenance_service.query_entity_lineage(entity_id)
    if not lineage:
        raise HTTPException(status_code=404, detail="No lineage found for entity")
    return lineage


@router.get("/source/{source_id}/derivations", response_model=SourceDerivationsResponse)
async def get_source_derivations(source_id: str):
    """查询来源的所有派生实体"""
    derivations = await provenance_service.query_source_derivations(source_id)
    return {"derivations": derivations, "count": len(derivations)}


@router.get("/entity/{entity_id}/evidence", response_model=EvidenceCollectionResponse)
async def collect_entity_evidence(entity_id: str):
    """收集实体的所有证据"""
    evidence_list = await provenance_service.collect_evidence_for_entity(entity_id)
    return {"evidence": evidence_list, "count": len(evidence_list)}


@router.get("/entity/{entity_id}/completeness", response_model=LineageCompletenessResponse)
async def check_lineage_completeness(entity_id: str):
    """验证溯源链完整性"""
    result = await provenance_service.lineage_chain_completeness(entity_id)
    if not result:
        raise HTTPException(status_code=404, detail="Entity not found")
    return result
