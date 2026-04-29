from __future__ import annotations

from uuid import UUID

from sqlalchemy.orm import Session

from app.processing.pipeline import process_project_raw_items, signal_quality_summary
from app.services.common import parse_uuid


def process_project(
    db: Session,
    project_id: UUID | str,
    mode: str,
    reprocess: bool,
    force_invalid_llm_json: bool = False,
) -> dict[str, object]:
    parsed_project_id = project_id if isinstance(project_id, UUID) else parse_uuid(str(project_id), "project_id")
    return process_project_raw_items(
        db=db,
        project_id=parsed_project_id,
        mode=mode,
        reprocess=reprocess,
        force_invalid_llm_json=force_invalid_llm_json,
    )


def get_processing_summary(db: Session, project_id: UUID | str) -> dict[str, object]:
    parsed_project_id = project_id if isinstance(project_id, UUID) else parse_uuid(str(project_id), "project_id")
    return signal_quality_summary(db=db, project_id=parsed_project_id)
