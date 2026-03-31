from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from ..provenance import provenance_service

router = APIRouter(prefix="/provenance", tags=["provenance"])


# ============ Pydantic Request/Response Models ============


class CreateEvidenceRequest(BaseModel):
    content: str = Field(..., min_length=1, description="证据文本内容")
    source_name: str = Field(..., min_length=1, description="来源名称")
    page_reference: Optional[str] = Field(None, description="页码/章节引用")


class LinkSourceRequest(BaseModel):
    source_id: str = Field(..., min_length=1, description="来源节点 ID")


class EvidenceResponse(BaseModel):
    id: str = Field(description="证据节点 ID")
    content: str = Field(description="证据文本内容")
    source_name: str = Field(description="来源名称")
    page_reference: Optional[str] = Field(default=None, description="页码/章节引用")
    status: str = Field(default="pending", description="证据状态")


class LineageChainResponse(BaseModel):
    entity: dict = Field(description="实体节点")
    evidence: dict = Field(description="证据节点")
    source: dict = Field(description="来源节点")


class LineageCompletenessResponse(BaseModel):
    entity: dict = Field(description="实体节点")
    evidence: Optional[dict] = Field(default=None, description="证据节点")
    source: Optional[dict] = Field(default=None, description="来源节点")
    has_evidence: bool = Field(description="是否存在证据")
    has_source: bool = Field(description="是否存在来源")
    chain_complete: bool = Field(description="溯源链是否完整")


class EvidenceCollectionItem(BaseModel):
    evidence: dict = Field(description="证据节点")
    source: Optional[dict] = Field(default=None, description="来源节点")


# ============ Endpoints ============


@router.post("/evidence", response_model=EvidenceResponse)
async def create_evidence(request: CreateEvidenceRequest):
    """创建证据节点"""
    result = await provenance_service.create_evidence(
        content=request.content,
        source_name=request.source_name,
        page_reference=request.page_reference,
    )
    return result


@router.get("/evidence/{evidence_id}", response_model=EvidenceResponse)
async def get_evidence(evidence_id: str):
    """获取证据详情"""
    result = await provenance_service.get_evidence(evidence_id)
    if not result:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return result


@router.post("/evidence/{evidence_id}/link-source")
async def link_evidence_to_source(evidence_id: str, request: LinkSourceRequest):
    """关联证据与来源 (DERIVED_FROM 关系)"""
    result = await provenance_service.link_evidence_to_source(
        evidence_id=evidence_id,
        source_id=request.source_id,
    )
    return {"relationship": result, "message": "Evidence linked to source"}


@router.get("/entity/{entity_id}/lineage")
async def get_entity_lineage(entity_id: str):
    """查询实体溯源链: Entity -> Evidence -> Source"""
    lineage = await provenance_service.query_entity_lineage(entity_id)
    if not lineage:
        raise HTTPException(status_code=404, detail="No lineage found for entity")
    return lineage


@router.get("/source/{source_id}/derivations")
async def get_source_derivations(source_id: str):
    """查询来源的所有派生实体"""
    derivations = await provenance_service.query_source_derivations(source_id)
    return {"derivations": derivations, "count": len(derivations)}


@router.get("/entity/{entity_id}/evidence")
async def collect_entity_evidence(entity_id: str):
    """收集实体的所有证据"""
    evidence_list = await provenance_service.collect_evidence_for_entity(entity_id)
    return {"evidence": evidence_list, "count": len(evidence_list)}


@router.get("/entity/{entity_id}/completeness")
async def check_lineage_completeness(entity_id: str):
    """验证溯源链完整性"""
    result = await provenance_service.lineage_chain_completeness(entity_id)
    if not result:
        raise HTTPException(status_code=404, detail="Entity not found")
    return result
