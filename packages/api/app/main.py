from contextlib import asynccontextmanager
from typing import Any, cast

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .core import configure_logging, get_logger
from .core.config import get_settings
from .core.database import init_db
from .kg.db import init_kg_db
from .api.herb import router as herb_router
from .api.graph import router as graph_router
from .api.graph_agent import router as graph_agent_router
from .api.workbench import router as workbench_router
from .api.verification import router as verification_router
from .api.chat import router as chat_router
from .api.provenance import router as provenance_router
from .api.notification import router as notification_router
from .api.pipeline import router as pipeline_router
from .api.pipeline_review import router as pipeline_review_router
from .api.pipeline_export import router as pipeline_export_router

settings = get_settings()
configure_logging(settings)
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("初始化应用依赖")
    await init_db()
    await init_kg_db()
    logger.info("应用依赖初始化完成")
    yield


app = FastAPI(
    title=settings.app_name,
    debug=settings.debug,
    lifespan=lifespan,
)

app.add_middleware(
    cast(Any, CORSMiddleware),
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(herb_router, prefix=settings.api_prefix)
app.include_router(graph_router, prefix=settings.api_prefix)
app.include_router(graph_agent_router, prefix=settings.api_prefix)
app.include_router(workbench_router, prefix=settings.api_prefix)
app.include_router(verification_router, prefix=settings.api_prefix)
app.include_router(chat_router, prefix=settings.api_prefix)
app.include_router(provenance_router, prefix=settings.api_prefix)
app.include_router(notification_router, prefix=settings.api_prefix)
app.include_router(pipeline_router, prefix=settings.api_prefix)
app.include_router(pipeline_review_router, prefix=settings.api_prefix)
app.include_router(pipeline_export_router, prefix=settings.api_prefix)


@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": settings.app_name}
