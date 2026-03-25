from __future__ import annotations

from typing import Any, Protocol
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.review import ReviewItemModel, ReviewSessionModel
from app.pipeline.models import PipelineRun, PipelineStepKey
from app.pipeline.schemas import PipelineStepPreviewResponse
from app.pipeline.steps.base import PipelineStepContext, build_preview_response
from app.review.models import ReviewItem, ReviewItemDecision, ReviewSession, ReviewSessionStatus, review_now
from app.review.schemas import ReviewSummary


def _coerce_payload(payload: dict[str, Any]) -> dict[str, object]:
    return dict(payload or {})


def build_review_item_key(position: int, payload: dict[str, Any]) -> str:
    node_type = str(payload.get("type") or payload.get("node_type") or "node").lower()
    name = str(payload.get("name") or payload.get("node_name") or f"item-{position + 1}").strip()
    safe_name = name.replace(" ", "-")
    return f"{node_type}-{position + 1}-{safe_name}"


class ReviewStorage(Protocol):
    async def save_session(self, session: ReviewSession) -> ReviewSession: ...
    async def get_session(self, run_id: str) -> ReviewSession: ...
    async def get_session_or_none(self, run_id: str) -> ReviewSession | None: ...


class InMemoryReviewStorage:
    def __init__(self) -> None:
        self._sessions: dict[str, ReviewSession] = {}

    async def save_session(self, session: ReviewSession) -> ReviewSession:
        session.updated_at = review_now()
        self._sessions[session.run_id] = session.model_copy(deep=True)
        return session

    async def get_session(self, run_id: str) -> ReviewSession:
        try:
            return self._sessions[run_id].model_copy(deep=True)
        except KeyError as exc:
            raise KeyError(run_id) from exc

    async def get_session_or_none(self, run_id: str) -> ReviewSession | None:
        session = self._sessions.get(run_id)
        return session.model_copy(deep=True) if session else None


def _deserialize_session(session_model: ReviewSessionModel, item_models: list[ReviewItemModel]) -> ReviewSession:
    return ReviewSession(
        id=session_model.id,
        run_id=session_model.run_id,
        step=PipelineStepKey(session_model.step),
        status=ReviewSessionStatus(session_model.status),
        items=[
            ReviewItem(
                item_key=item_model.item_key,
                node_type=item_model.node_type,
                original_payload=dict(item_model.original_payload or {}),
                revised_payload=dict(item_model.revised_payload or {}),
                decision=ReviewItemDecision(item_model.decision),
                comment=item_model.comment,
            )
            for item_model in item_models
        ],
        comment=session_model.comment,
        confirmed_at=session_model.confirmed_at,
        created_at=session_model.created_at,
        updated_at=session_model.updated_at,
    )


class SQLAlchemyReviewStorage:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_session(self, session: ReviewSession) -> ReviewSession:
        model = await self.session.get(ReviewSessionModel, session.id)
        if model is None:
            existing_stmt = select(ReviewSessionModel).where(ReviewSessionModel.run_id == session.run_id)
            existing = (await self.session.execute(existing_stmt)).scalar_one_or_none()
            if existing is not None:
                await self.session.execute(delete(ReviewItemModel).where(ReviewItemModel.session_id == existing.id))
                model = existing
            else:
                model = ReviewSessionModel(id=session.id, run_id=session.run_id)
                self.session.add(model)

        model.id = session.id
        model.run_id = session.run_id
        model.step = session.step.value
        model.status = session.status.value
        model.comment = session.comment
        model.confirmed_at = session.confirmed_at
        model.updated_at = review_now()

        await self.session.execute(delete(ReviewItemModel).where(ReviewItemModel.session_id == model.id))
        for position, item in enumerate(session.items):
            self.session.add(
                ReviewItemModel(
                    session_id=model.id,
                    position=position,
                    item_key=item.item_key,
                    node_type=item.node_type,
                    original_payload=item.original_payload,
                    revised_payload=item.revised_payload,
                    decision=item.decision.value,
                    comment=item.comment,
                )
            )

        await self.session.commit()
        return session

    async def get_session(self, run_id: str) -> ReviewSession:
        session = await self.get_session_or_none(run_id)
        if session is None:
            raise KeyError(run_id)
        return session

    async def get_session_or_none(self, run_id: str) -> ReviewSession | None:
        session_stmt = select(ReviewSessionModel).where(ReviewSessionModel.run_id == run_id)
        session_model = (await self.session.execute(session_stmt)).scalar_one_or_none()
        if session_model is None:
            return None

        item_stmt = (
            select(ReviewItemModel)
            .where(ReviewItemModel.session_id == session_model.id)
            .order_by(ReviewItemModel.position.asc(), ReviewItemModel.id.asc())
        )
        item_models = list((await self.session.execute(item_stmt)).scalars().all())
        return _deserialize_session(session_model, item_models)


class ReviewService:
    def __init__(self, storage: ReviewStorage | None = None) -> None:
        self.storage = storage or InMemoryReviewStorage()

    async def create_or_refresh_session(self, run: PipelineRun) -> ReviewSession:
        mapping_payload = run.steps[PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL].preview_payload
        validation = dict(mapping_payload.get("validation") or {})
        if validation.get("is_valid") is not True:
            raise ValueError("共享模型映射未通过校验，不能创建人工确认会话")

        nodes = mapping_payload.get("nodes", [])
        items = []
        for position, node in enumerate(nodes):
            if not isinstance(node, dict):
                continue
            items.append(
                ReviewItem(
                    item_key=build_review_item_key(position, node),
                    node_type=str(node.get("type") or ""),
                    original_payload=_coerce_payload(node),
                    revised_payload=_coerce_payload(node),
                )
            )

        existing = await self.storage.get_session_or_none(run.id)
        session = ReviewSession(
            id=existing.id if existing else f"review-{uuid4()}",
            run_id=run.id,
            items=items,
            comment=existing.comment if existing else None,
        )
        return await self.storage.save_session(session)

    async def get_session(self, run_id: str) -> ReviewSession:
        return await self.storage.get_session(run_id)

    async def get_session_or_none(self, run_id: str) -> ReviewSession | None:
        return await self.storage.get_session_or_none(run_id)

    async def update_item(
        self,
        *,
        run_id: str,
        item_key: str,
        decision: ReviewItemDecision | None = None,
        revised_payload: dict[str, Any] | None = None,
        comment: str | None = None,
    ) -> ReviewSession:
        session = await self.get_session(run_id)
        for item in session.items:
            if item.item_key != item_key:
                continue
            if decision is not None:
                item.decision = decision
            if revised_payload is not None:
                item.revised_payload = _coerce_payload(revised_payload)
            if comment is not None:
                item.comment = comment
            session.status = ReviewSessionStatus.DRAFT
            session.confirmed_at = None
            return await self.storage.save_session(session)
        raise KeyError(item_key)

    async def confirm_session(self, run_id: str, comment: str | None = None) -> ReviewSession:
        session = await self.get_session(run_id)
        if any(item.decision == ReviewItemDecision.PENDING for item in session.items):
            raise ValueError("仍有待处理的人工确认条目，不能锁定会话")
        session.status = ReviewSessionStatus.CONFIRMED
        session.comment = comment or session.comment
        session.confirmed_at = review_now()
        return await self.storage.save_session(session)

    def summarize_session(self, session: ReviewSession) -> ReviewSummary:
        decisions = [item.decision for item in session.items]
        return ReviewSummary(
            status=session.status,
            total_items=len(session.items),
            pending_items=sum(1 for item in decisions if item == ReviewItemDecision.PENDING),
            confirmed_items=sum(1 for item in decisions if item == ReviewItemDecision.CONFIRM),
            edited_items=sum(1 for item in decisions if item == ReviewItemDecision.EDIT),
            rejected_items=sum(1 for item in decisions if item == ReviewItemDecision.REJECT),
        )

    async def build_preview(self, run: PipelineRun, context: PipelineStepContext) -> PipelineStepPreviewResponse:
        mapping_payload = run.steps[PipelineStepKey.MAP_TO_KNOWLEDGE_MODEL].preview_payload
        validation = dict(mapping_payload.get("validation") or {})
        if validation.get("is_valid") is not True:
            blocking_issues = ["共享模型映射未通过校验，需先修正候选实体"]
            return build_preview_response(
                context=context,
                step=PipelineStepKey.HUMAN_REVIEW,
                summary="人工确认前仍有阻塞项",
                preview_kind="review_decision",
                preview_payload={"blocking_issues": blocking_issues, "review_items": []},
                errors=blocking_issues,
                next_step_ready=False,
            )

        session = await self.get_session_or_none(run.id)
        if session is None:
            session = await self.create_or_refresh_session(run)
        summary = self.summarize_session(session)
        preview_items = [
            {
                "item_key": item.item_key,
                "node_type": item.node_type,
                "decision": item.decision.value,
                "original_payload": item.original_payload,
                "revised_payload": item.revised_payload,
                "comment": item.comment,
            }
            for item in session.items
        ]
        return build_preview_response(
            context=context,
            step=PipelineStepKey.HUMAN_REVIEW,
            summary="人工确认清单已生成" if session.status != ReviewSessionStatus.CONFIRMED else "人工确认清单已锁定",
            preview_kind="review_decision",
            preview_payload={
                "review_session_id": session.id,
                "session_status": session.status.value,
                "summary": summary.model_dump(mode="json"),
                "review_items": preview_items,
                "blocking_issues": [],
            },
            next_step_ready=session.status == ReviewSessionStatus.CONFIRMED,
        )
