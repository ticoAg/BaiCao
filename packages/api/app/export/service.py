from __future__ import annotations

import hashlib
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Protocol

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from graph_schema.constants import EdgeType, NodeStatus, parse_node_type, to_neo4j_label
from graph_schema.import_records import GraphImportEdge, GraphImportRecord

from app.export.models import ExportRecord, ExportRecordStatus, GraphWriteResult, GraphWriteStatus, export_now
from app.export.schemas import ExportPlanResponse
from app.exporters.jsonl_exporter import JSONLExporter
from app.kg.db import cypher_query
from app.models.export import ExportRecordModel
from app.pipeline.models import PipelineRun, PipelineStepKey, PipelineStepStatus
from app.pipeline.schemas import PipelineStepPreviewResponse
from app.pipeline.steps.base import PipelineStepContext, build_preview_response
from app.review.models import ReviewItemDecision, ReviewSessionStatus
from app.review.service import ReviewService
from app.storage.objects.base import ObjectStorage
from app.storage.objects.memory import InMemoryObjectStorage


def _record_properties(payload: dict[str, object]) -> dict[str, object]:
    ignored_keys = {"id", "name", "node_name", "type", "node_type", "label", "source", "status", "imported_at", "edges"}
    return {key: value for key, value in payload.items() if key not in ignored_keys}


def _deserialize_export_record(model: ExportRecordModel) -> ExportRecord:
    return ExportRecord(
        id=model.id,
        run_id=model.run_id,
        review_session_id=model.review_session_id,
        status=ExportRecordStatus(model.status),
        graph_write_status=GraphWriteStatus(model.graph_write_status),
        snapshot_bucket=model.snapshot_bucket,
        snapshot_object_key=model.snapshot_object_key,
        snapshot_checksum=model.snapshot_checksum,
        snapshot_size=model.snapshot_size,
        error_message=model.error_message,
        retry_count=model.retry_count,
        executed_at=model.executed_at,
        completed_at=model.completed_at,
        created_at=model.created_at,
        updated_at=model.updated_at,
    )


class ExportStorage(Protocol):
    async def save_record(self, record: ExportRecord) -> ExportRecord: ...
    async def get_record(self, export_id: str) -> ExportRecord: ...
    async def get_latest_record(self, run_id: str) -> ExportRecord | None: ...


class InMemoryExportStorage:
    def __init__(self) -> None:
        self._records: dict[str, ExportRecord] = {}

    async def save_record(self, record: ExportRecord) -> ExportRecord:
        record.updated_at = export_now()
        self._records[record.id] = record.model_copy(deep=True)
        return record

    async def get_record(self, export_id: str) -> ExportRecord:
        try:
            return self._records[export_id].model_copy(deep=True)
        except KeyError as exc:
            raise KeyError(export_id) from exc

    async def get_latest_record(self, run_id: str) -> ExportRecord | None:
        records = [record for record in self._records.values() if record.run_id == run_id]
        if not records:
            return None
        latest = max(records, key=lambda item: item.created_at)
        return latest.model_copy(deep=True)


class SQLAlchemyExportStorage:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def save_record(self, record: ExportRecord) -> ExportRecord:
        model = await self.session.get(ExportRecordModel, record.id)
        if model is None:
            model = ExportRecordModel(id=record.id)
            self.session.add(model)

        model.run_id = record.run_id
        model.review_session_id = record.review_session_id
        model.status = record.status.value
        model.graph_write_status = record.graph_write_status.value
        model.snapshot_bucket = record.snapshot_bucket
        model.snapshot_object_key = record.snapshot_object_key
        model.snapshot_checksum = record.snapshot_checksum
        model.snapshot_size = record.snapshot_size
        model.error_message = record.error_message
        model.retry_count = record.retry_count
        model.executed_at = record.executed_at
        model.completed_at = record.completed_at
        model.updated_at = export_now()

        await self.session.commit()
        return record

    async def get_record(self, export_id: str) -> ExportRecord:
        model = await self.session.get(ExportRecordModel, export_id)
        if model is None:
            raise KeyError(export_id)
        return _deserialize_export_record(model)

    async def get_latest_record(self, run_id: str) -> ExportRecord | None:
        stmt = (
            select(ExportRecordModel)
            .where(ExportRecordModel.run_id == run_id)
            .order_by(ExportRecordModel.created_at.desc(), ExportRecordModel.id.desc())
            .limit(1)
        )
        model = (await self.session.execute(stmt)).scalar_one_or_none()
        return _deserialize_export_record(model) if model else None


class GraphWriter(Protocol):
    async def write_records(self, records: list[GraphImportRecord]) -> GraphWriteResult: ...


class InMemoryGraphWriter:
    def __init__(self) -> None:
        self.records: list[GraphImportRecord] = []

    async def write_records(self, records: list[GraphImportRecord]) -> GraphWriteResult:
        self.records.extend(records)
        return GraphWriteResult(nodes_written=len(records), edges_written=sum(len(record.edges) for record in records))


class FailingGraphWriter:
    def __init__(self, error: Exception) -> None:
        self.error = error

    async def write_records(self, records: list[GraphImportRecord]) -> GraphWriteResult:
        raise self.error


class Neo4jGraphWriter:
    async def write_records(self, records: list[GraphImportRecord]) -> GraphWriteResult:
        nodes_written = 0
        edges_written = 0

        for record in records:
            if record.node_type is None:
                continue
            label = to_neo4j_label(getattr(record.node_type, "value", record.node_type))
            node_props = {
                "name": record.node_name,
                "source": record.source,
                "status": getattr(record.status, "value", record.status),
                "imported_at": export_now().isoformat(),
                **record.properties,
            }
            await cypher_query(
                f"""
                MERGE (n:{label} {{name: $name}})
                SET n += $props
                SET n.id = coalesce(n.id, $node_id)
                RETURN n
                """,
                {
                    "name": record.node_name,
                    "node_id": f"{label.lower()}-{record.node_name}",
                    "props": node_props,
                },
            )
            nodes_written += 1

            for edge in record.edges:
                rel_type = EdgeType(getattr(edge.type, "value", edge.type)).value
                rel_props = {"status": NodeStatus.PENDING.value, **edge.properties}
                import_scope_key = rel_props.get("import_scope_key")
                merge_fragment = " {import_scope_key: $import_scope_key}" if import_scope_key else ""
                await cypher_query(
                    f"""
                    MATCH (source {{name: $source_name}})
                    MATCH (target {{name: $target_name}})
                    MERGE (source)-[r:{rel_type}{merge_fragment}]->(target)
                    SET r += $props
                    RETURN r
                    """,
                    {
                        "source_name": record.node_name,
                        "target_name": edge.target,
                        "import_scope_key": import_scope_key,
                        "props": rel_props,
                    },
                )
                edges_written += 1

        return GraphWriteResult(nodes_written=nodes_written, edges_written=edges_written)


def _parse_jsonl_records(content: bytes) -> list[GraphImportRecord]:
    lines = [line for line in content.decode("utf-8").splitlines() if line.strip()]
    return [GraphImportRecord.model_validate_json(line) for line in lines]


class ExportService:
    def __init__(
        self,
        *,
        storage: ExportStorage | None = None,
        review_service: ReviewService,
        object_storage: ObjectStorage | None = None,
        graph_writer: GraphWriter | None = None,
        snapshot_bucket: str = "baicao-pipeline-exports",
    ) -> None:
        self.storage = storage or InMemoryExportStorage()
        self.review_service = review_service
        self.object_storage = object_storage or InMemoryObjectStorage()
        self.graph_writer = graph_writer or InMemoryGraphWriter()
        self.snapshot_bucket = snapshot_bucket

    async def build_export_plan_payload(self, run: PipelineRun) -> ExportPlanResponse:
        review_session = await self.review_service.get_session_or_none(run.id)
        latest = await self.storage.get_latest_record(run.id)
        if review_session is None or review_session.status != ReviewSessionStatus.CONFIRMED:
            return ExportPlanResponse(
                run_id=run.id,
                export_targets=["jsonl_snapshot", "neo4j"],
                blocking_issues=["人工确认会话尚未确认，不能生成真实导出计划"],
                latest_execution=self._response_from_record(latest) if latest else None,
            )

        records = self._records_from_review(run, review_session)
        return ExportPlanResponse(
            run_id=run.id,
            review_session_id=review_session.id,
            export_targets=["jsonl_snapshot", "neo4j"],
            record_count=len(records),
            records=[record.model_dump(mode="json") for record in records],
            latest_execution=self._response_from_record(latest) if latest else None,
        )

    async def build_preview(self, run: PipelineRun, context: PipelineStepContext) -> PipelineStepPreviewResponse:
        plan = await self.build_export_plan_payload(run)
        return build_preview_response(
            context=context,
            step=PipelineStepKey.EXPORT,
            summary="导出/入库预览已生成" if not plan.blocking_issues else "导出/入库预览存在阻塞",
            preview_kind="export_plan",
            preview_payload=plan.model_dump(mode="json"),
            errors=plan.blocking_issues,
            next_step_ready=not plan.blocking_issues,
        )

    async def execute_export(self, run: PipelineRun) -> ExportRecord:
        if run.steps[PipelineStepKey.EXPORT].status != PipelineStepStatus.CONFIRMED:
            raise ValueError("export 步骤尚未确认，不能执行真实导出")

        review_session = await self.review_service.get_session(run.id)
        if review_session.status != ReviewSessionStatus.CONFIRMED:
            raise ValueError("人工确认会话尚未确认，不能执行真实导出")

        records = self._records_from_review(run, review_session)
        record = ExportRecord(run_id=run.id, review_session_id=review_session.id, executed_at=export_now())
        await self.storage.save_record(record)

        try:
            snapshot_bytes = self._serialize_records(records)
            checksum = hashlib.sha256(snapshot_bytes).hexdigest()
            object_key = f"pipeline-exports/{run.id}/{record.id}/snapshot.jsonl"
            stored = self.object_storage.put_jsonl(
                bucket=self.snapshot_bucket,
                key=object_key,
                content=snapshot_bytes,
                metadata={"run_id": run.id, "review_session_id": review_session.id, "checksum": checksum},
            )
            record.snapshot_bucket = stored.bucket
            record.snapshot_object_key = stored.key
            record.snapshot_size = stored.size
            record.snapshot_checksum = checksum
            record.status = ExportRecordStatus.SNAPSHOT_WRITTEN
            await self.storage.save_record(record)
        except Exception as exc:
            record.status = ExportRecordStatus.FAILED
            record.graph_write_status = GraphWriteStatus.FAILED
            record.error_message = str(exc)
            await self.storage.save_record(record)
            return record

        try:
            await self.graph_writer.write_records(records)
            record.status = ExportRecordStatus.COMPLETED
            record.graph_write_status = GraphWriteStatus.SUCCEEDED
            record.error_message = None
            record.completed_at = export_now()
        except Exception as exc:
            record.status = ExportRecordStatus.PARTIAL_FAILED
            record.graph_write_status = GraphWriteStatus.FAILED
            record.error_message = str(exc)

        await self.storage.save_record(record)
        return record

    async def retry_graph_write(self, export_id: str) -> ExportRecord:
        record = await self.storage.get_record(export_id)
        if not record.snapshot_bucket or not record.snapshot_object_key:
            raise ValueError("当前导出记录没有可补写的 JSONL 快照")

        snapshot_bytes = self.object_storage.get_object(record.snapshot_bucket, record.snapshot_object_key)
        records = _parse_jsonl_records(snapshot_bytes)
        record.retry_count += 1
        try:
            await self.graph_writer.write_records(records)
            record.status = ExportRecordStatus.COMPLETED
            record.graph_write_status = GraphWriteStatus.SUCCEEDED
            record.error_message = None
            record.completed_at = export_now()
        except Exception as exc:
            record.status = ExportRecordStatus.PARTIAL_FAILED
            record.graph_write_status = GraphWriteStatus.FAILED
            record.error_message = str(exc)

        await self.storage.save_record(record)
        return record

    async def get_latest_record(self, run_id: str) -> ExportRecord | None:
        return await self.storage.get_latest_record(run_id)

    def _records_from_review(self, run: PipelineRun, review_session) -> list[GraphImportRecord]:
        records: list[GraphImportRecord] = []
        for item in review_session.items:
            if item.decision == ReviewItemDecision.REJECT:
                continue

            payload = item.revised_payload if item.revised_payload else item.original_payload
            node_type_value = payload.get("type") or payload.get("node_type")
            node_name = payload.get("name") or payload.get("node_name")
            if not node_type_value or not node_name:
                continue

            edges_payload = payload.get("edges") if isinstance(payload.get("edges"), list) else []
            edges = [
                GraphImportEdge(
                    type=EdgeType(str(edge.get("type"))),
                    target=str(edge.get("target")),
                    properties=dict(edge.get("properties") or {}),
                )
                for edge in edges_payload
                if isinstance(edge, dict) and edge.get("type") and edge.get("target")
            ]
            records.append(
                GraphImportRecord(
                    node_type=parse_node_type(str(node_type_value)),
                    node_name=str(node_name),
                    source=str(payload.get("source") or run.source_locator),
                    status=NodeStatus.PENDING,
                    properties=_record_properties(payload),
                    edges=edges,
                )
            )
        return records

    def _serialize_records(self, records: list[GraphImportRecord]) -> bytes:
        with NamedTemporaryFile(suffix=".jsonl", delete=False) as handle:
            temp_path = Path(handle.name)
        try:
            JSONLExporter().export(records, str(temp_path))
            return temp_path.read_bytes()
        finally:
            temp_path.unlink(missing_ok=True)

    def _response_from_record(self, record: ExportRecord):
        from app.export.schemas import ExportRecordResponse

        return ExportRecordResponse(
            id=record.id,
            run_id=record.run_id,
            review_session_id=record.review_session_id,
            status=record.status.value,
            graph_write_status=record.graph_write_status.value,
            snapshot_bucket=record.snapshot_bucket,
            snapshot_object_key=record.snapshot_object_key,
            snapshot_checksum=record.snapshot_checksum,
            snapshot_size=record.snapshot_size,
            error_message=record.error_message,
            retry_count=record.retry_count,
        )
