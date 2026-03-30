from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.export.service import ExportService, Neo4jGraphWriter, SQLAlchemyExportStorage
from app.pipeline.materialization import SourceMaterializationService
from app.pipeline.service import PipelineService
from app.pipeline.storage import SQLAlchemyPipelineStorage
from app.pipeline.uploads import SourceUploadService
from app.review.service import ReviewService, SQLAlchemyReviewStorage
from app.storage.objects import build_object_storage


async def get_review_service(db: AsyncSession = Depends(get_db)) -> ReviewService:
    return ReviewService(storage=SQLAlchemyReviewStorage(db))


async def get_export_service(
    db: AsyncSession = Depends(get_db),
    review_service: ReviewService = Depends(get_review_service),
) -> ExportService:
    settings = get_settings()
    return ExportService(
        storage=SQLAlchemyExportStorage(db),
        review_service=review_service,
        object_storage=build_object_storage(settings),
        graph_writer=Neo4jGraphWriter(),
        snapshot_bucket=settings.object_storage_bucket,
    )


async def get_pipeline_service(
    db: AsyncSession = Depends(get_db),
    review_service: ReviewService = Depends(get_review_service),
    export_service: ExportService = Depends(get_export_service),
) -> PipelineService:
    settings = get_settings()
    return PipelineService(
        storage=SQLAlchemyPipelineStorage(db),
        review_service=review_service,
        export_service=export_service,
        materialization_service=SourceMaterializationService(settings.pipeline_source_storage_dir),
    )


def get_source_upload_service() -> SourceUploadService:
    settings = get_settings()
    return SourceUploadService(storage_root=settings.pipeline_source_storage_dir)
