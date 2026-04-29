from fastapi import FastAPI, HTTPException
from fastapi.exceptions import RequestValidationError

from app.api.errors import ApiError, api_error_handler, http_exception_handler, validation_error_handler
from app.api.routes import (
    clusters,
    collection_jobs,
    collection_logs,
    keywords,
    opportunities,
    projects,
    reports,
    settings,
    signals,
)

app = FastAPI(title="SignalForge API", version="0.1.0-phase-2")
app.add_exception_handler(ApiError, api_error_handler)
app.add_exception_handler(HTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_error_handler)

app.include_router(projects.router)
app.include_router(keywords.router)
app.include_router(collection_jobs.router)
app.include_router(collection_logs.router)
app.include_router(signals.router)
app.include_router(clusters.router)
app.include_router(opportunities.router)
app.include_router(reports.router)
app.include_router(settings.router)


@app.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "service": "signalforge-api",
        "phase": "phase-2-backend-api",
    }
