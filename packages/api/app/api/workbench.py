from fastapi import APIRouter

from ..schemas.workbench import (
    CypherValidationRequest,
    CypherValidationResult,
    WorkbenchExecuteRequest,
    WorkbenchExecuteResponse,
)
from ..services.workbench_service import workbench_service


router = APIRouter(prefix="/workbench", tags=["workbench"])


@router.post("/execute", response_model=WorkbenchExecuteResponse)
async def execute_workbench_command(payload: WorkbenchExecuteRequest):
    return await workbench_service.execute(payload.command, source=payload.source)


@router.post("/validate-cypher", response_model=CypherValidationResult)
async def validate_cypher(payload: CypherValidationRequest):
    return await workbench_service.validate_cypher(payload.query)
