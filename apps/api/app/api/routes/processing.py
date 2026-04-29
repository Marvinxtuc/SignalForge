from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter

from app.api.deps import DbSession
from app.api.errors import phase_not_available
from app.schemas.processing import ProcessingRequest, ProcessingResponse, ProcessingSummary
from app.services import processing_pipeline


router = APIRouter(tags=["processing"])

ALLOWED_PROCESSING_MODES = {"mock", "fallback_only"}
MANUAL_ONLY_MESSAGE = "Real LLM and embedding providers are manual-only in Phase 5."


@router.post("/api/projects/{project_id}/process", response_model=ProcessingResponse)
def process_project(project_id: UUID, payload: ProcessingRequest, db: DbSession) -> ProcessingResponse:
    if payload.mode not in ALLOWED_PROCESSING_MODES:
        raise phase_not_available(MANUAL_ONLY_MESSAGE, {"mode": payload.mode})

    summary = processing_pipeline.process_project(
        db=db,
        project_id=project_id,
        mode=payload.mode,
        reprocess=payload.reprocess,
    )
    return ProcessingResponse(project_id=project_id, **summary)


@router.get("/api/projects/{project_id}/processing-summary", response_model=ProcessingSummary)
def get_processing_summary(project_id: UUID, db: DbSession) -> ProcessingSummary:
    return ProcessingSummary(**processing_pipeline.get_processing_summary(db=db, project_id=project_id))
