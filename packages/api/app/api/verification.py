from __future__ import annotations
from typing import Optional
from uuid import UUID
from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from ..core.database import get_db
from ..models import (
    VerificationEvidenceModel,
    VerificationModel,
    VerificationStatus,
    UserModel,
    UserRole,
)
from ..kg.graph_service import graph_service

router = APIRouter(prefix="/verifications", tags=["verifications"])


# ============ Pydantic Request/Response Models ============

class EvidenceItem(BaseModel):
    """Evidence item schema"""
    source_id: UUID = Field(description="来源标识")
    quote: str = Field(description="证据引文")
    page_reference: Optional[str] = Field(default=None, description="页码或章节引用")
    relevance_score: float = Field(default=1.0, ge=0.0, le=1.0, description="证据相关度")


class CreateVerificationRequest(BaseModel):
    """Request model for creating a verification"""
    entity_type: str = Field(description="待验证实体类型")
    entity_id: str = Field(description="待验证实体标识")
    claimed_value: str = Field(description="待验证字段值")
    applicant_id: Optional[UUID] = Field(default=None, description="申请人标识")
    source_id: Optional[UUID] = Field(default=None, description="来源标识")
    field_name: Optional[str] = Field(default=None, description="待验证字段名")
    evidence: Optional[list[dict]] = Field(default=None, description="附带证据列表")


class VerificationResponse(BaseModel):
    """Response model for verification data"""
    model_config = ConfigDict(from_attributes=True)

    id: UUID = Field(description="验证记录标识")
    entity_type: str = Field(description="待验证实体类型")
    entity_id: str = Field(description="待验证实体标识")
    field_name: Optional[str] = Field(default=None, description="待验证字段名")
    claimed_value: str = Field(description="待验证字段值")
    source_id: Optional[UUID] = Field(default=None, description="来源标识")
    status: str = Field(description="验证状态")
    applicant_id: UUID = Field(description="申请人标识")
    verifier_id: Optional[UUID] = Field(default=None, description="审核人标识")
    verdict: Optional[str] = Field(default=None, description="裁决说明")
    verified_at: Optional[datetime] = Field(default=None, description="验证完成时间")
    created_at: datetime = Field(description="创建时间")


class PaginatedVerificationsResponse(BaseModel):
    """Paginated response for list of verifications"""
    items: list[VerificationResponse] = Field(description="当前页验证记录列表")
    total: int = Field(description="验证记录总数")
    page: int = Field(description="当前页码")
    page_size: int = Field(description="每页条目数")
    has_more: bool = Field(description="是否还有更多数据")


# ============ Helper Functions ============

async def _create_verification_record(
    db: AsyncSession,
    entity_type: str,
    entity_id: str,
    claimed_value: str,
    applicant_id: UUID,
    field_name: Optional[str] = None,
    source_id: Optional[UUID] = None,
    evidence: Optional[list[dict]] = None
) -> VerificationModel:
    """
    Helper function to create a verification record with evidence.

    Refactoring: Extract verification creation logic into a reusable helper method.
    """
    verification = VerificationModel(
        entity_type=entity_type,
        entity_id=entity_id,
        field_name=field_name,
        claimed_value=claimed_value,
        source_id=source_id,
        status="pending",
        applicant_id=applicant_id,
    )
    db.add(verification)
    await db.flush()

    # Add evidence if provided
    if evidence:
        for ev in evidence:
            ve = VerificationEvidenceModel(
                verification_id=verification.id,
                source_id=UUID(ev["source_id"]),
                quote=ev["quote"],
                page_reference=ev.get("page_reference"),
                relevance_score=ev.get("relevance_score", 1.0)
            )
            db.add(ve)

    await db.commit()
    await db.refresh(verification)
    return verification


async def _resolve_active_user_id(db: AsyncSession, role: Optional[UserRole] = None) -> UUID:
    """Resolve a default active user for demo-mode actions."""
    query = select(UserModel).where(UserModel.is_active.is_(True))
    if role is not None:
        query = query.where(UserModel.role == role)

    result = await db.execute(query.limit(1))
    user = result.scalar_one_or_none()
    if user:
        return user.id

    if role is not None:
        fallback = await db.execute(
            select(UserModel).where(UserModel.is_active.is_(True)).limit(1)
        )
        user = fallback.scalar_one_or_none()
        if user:
            return user.id

    raise HTTPException(
        status_code=400,
        detail="No active demo user available. Please seed demo data first.",
    )


def _update_verification_status(
    verification: VerificationModel,
    new_status: VerificationStatus,
    verifier_id: UUID,
    verdict: str
) -> None:
    """
    Helper function to update verification status.

    Refactoring: Extract status update logic into a reusable helper method.
    """
    verification.status = new_status
    verification.verifier_id = verifier_id
    verification.verdict = verdict
    verification.verified_at = datetime.now(UTC)


async def _sync_neo4j_for_verification(
    verification: VerificationModel,
    verification_id: UUID,
    verifier_id: UUID,
    status: str
) -> None:
    """
    Sync verification status to Neo4j graph database.
    """
    if status == "verified" and verification.entity_type == "herb":
        await graph_service.verify_node(
            verification.entity_id,
            str(verification_id),
            str(verifier_id),
            "verified"
        )
    elif status == "verified" and verification.entity_type in ["efficacy", "flavor", "meridian", "component"]:
        # Relation verification requires from_id, to_id, rel_type
        # Simplified handling - actual implementation needs parsing from entity_id
        pass


# ============ API Endpoints ============

@router.post("/", response_model=VerificationResponse)
async def create_verification(
    request: Request,
    entity_type: Optional[str] = Query(None),
    entity_id: Optional[str] = Query(None),
    claimed_value: Optional[str] = Query(None),
    applicant_id: Optional[UUID] = Query(None),
    source_id: Optional[UUID] = Query(None),
    field_name: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """创建验证申请"""
    raw_body = await request.body()
    payload = CreateVerificationRequest.model_validate_json(raw_body) if raw_body else None

    if payload is not None:
        entity_type = payload.entity_type
        entity_id = payload.entity_id
        claimed_value = payload.claimed_value
        applicant_id = payload.applicant_id
        source_id = payload.source_id
        field_name = payload.field_name
        evidence = payload.evidence
    else:
        evidence = None

    if not entity_type or not entity_id or not claimed_value:
        raise HTTPException(
            status_code=422,
            detail="entity_type, entity_id and claimed_value are required",
        )

    resolved_applicant_id = applicant_id or await _resolve_active_user_id(db, UserRole.USER)

    verification = await _create_verification_record(
        db=db,
        entity_type=entity_type,
        entity_id=entity_id,
        claimed_value=claimed_value,
        applicant_id=resolved_applicant_id,
        field_name=field_name,
        source_id=source_id,
        evidence=evidence
    )
    return verification


@router.get("/{verification_id}", response_model=VerificationResponse)
async def get_verification(
    verification_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """获取验证详情"""
    result = await db.execute(
        select(VerificationModel).where(VerificationModel.id == verification_id)
    )
    verification = result.scalar_one_or_none()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")
    return verification


@router.get("/", response_model=PaginatedVerificationsResponse)
async def list_verifications(
    status: Optional[str] = Query(None),
    entity_type: Optional[str] = Query(None),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db)
):
    """列出验证申请"""
    query = select(VerificationModel)
    count_query = select(func.count(VerificationModel.id))

    if status:
        query = query.where(VerificationModel.status == status)
        count_query = count_query.where(VerificationModel.status == status)
    if entity_type:
        query = query.where(VerificationModel.entity_type == entity_type)
        count_query = count_query.where(VerificationModel.entity_type == entity_type)

    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    count_result = await db.execute(count_query)

    items = list(result.scalars().all())
    total = count_result.scalar()

    return {
        "items": items,
        "total": total,
        "page": offset // limit + 1,
        "page_size": limit,
        "has_more": offset + len(items) < total
    }


@router.post("/{verification_id}/verify", response_model=VerificationResponse)
async def verify_verification(
    verification_id: UUID,
    verifier_id: Optional[UUID] = None,
    status: str = Query(..., pattern="^(verified|rejected)$"),
    verdict: str = Query(...),
    db: AsyncSession = Depends(get_db)
):
    """专家验证"""
    # Fetch verification record
    result = await db.execute(
        select(VerificationModel).where(VerificationModel.id == verification_id)
    )
    verification = result.scalar_one_or_none()
    if not verification:
        raise HTTPException(status_code=404, detail="Verification not found")

    if verification.status != "pending":
        raise HTTPException(status_code=400, detail="Verification is not pending")

    # Update verification status using helper
    resolved_verifier_id = verifier_id or await _resolve_active_user_id(db, UserRole.EXPERT)

    _update_verification_status(
        verification=verification,
        new_status=VerificationStatus(status),
        verifier_id=resolved_verifier_id,
        verdict=verdict
    )

    await db.commit()

    # Sync to Neo4j
    await _sync_neo4j_for_verification(
        verification=verification,
        verification_id=verification_id,
        verifier_id=resolved_verifier_id,
        status=status
    )

    await db.refresh(verification)
    return verification
