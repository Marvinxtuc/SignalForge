from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter

from app.api.deps import DbSession
from app.schemas.reports import CsvReportResponse, MarkdownReportResponse, ReportRequest
from app.services import reports as report_service


router = APIRouter(tags=["reports"])


@router.post("/api/projects/{project_id}/reports/markdown", response_model=MarkdownReportResponse)
def export_markdown_report(
    project_id: UUID,
    request: ReportRequest,
    db: DbSession,
) -> MarkdownReportResponse:
    return MarkdownReportResponse(
        content=report_service.generate_markdown_report(db, project_id, request),
        generated_at=datetime.now(timezone.utc),
    )


@router.post("/api/projects/{project_id}/reports/csv", response_model=CsvReportResponse)
def export_csv_report(
    project_id: UUID,
    request: ReportRequest,
    db: DbSession,
) -> CsvReportResponse:
    return CsvReportResponse(
        filename=f"signalforge-{project_id}-signals.csv",
        content=report_service.generate_csv_report(db, project_id, request),
        generated_at=datetime.now(timezone.utc),
    )
