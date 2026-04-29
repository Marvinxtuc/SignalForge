from __future__ import annotations

from datetime import datetime

from pydantic import Field

from app.schemas.common import ApiSchema


class ReportRequest(ApiSchema):
    days: int = Field(default=7, ge=1, le=365)
    min_pain_level: int = Field(default=70, ge=0, le=100)
    top_clusters_limit: int = Field(default=5, ge=1, le=50)
    opportunities_limit: int = Field(default=10, ge=1, le=100)


class MarkdownReportResponse(ApiSchema):
    format: str = "markdown"
    content: str
    generated_at: datetime


class CsvReportResponse(ApiSchema):
    format: str = "csv"
    filename: str
    content_type: str = "text/csv"
    content: str
    generated_at: datetime
