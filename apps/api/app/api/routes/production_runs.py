from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from app.api.deps import DbSession, PaginationDep
from app.schemas.common import PaginatedResponse
from app.schemas.production_runs import ProductionRunCloseout, ProductionRunCreate, ProductionRunRead
from app.services import production_runs as production_run_service
from app.services.common import paginated_response


router = APIRouter(prefix="/api/production/runs", tags=["production"])


@router.get("", response_model=PaginatedResponse[ProductionRunRead])
def list_production_runs(db: DbSession, pagination: PaginationDep) -> PaginatedResponse[ProductionRunRead]:
    runs, total = production_run_service.list_runs(db, pagination)
    return paginated_response(runs, pagination, total)


@router.post("", response_model=ProductionRunRead, status_code=status.HTTP_201_CREATED)
def create_production_run(payload: ProductionRunCreate, db: DbSession) -> ProductionRunRead:
    return production_run_service.create_run(db, payload)


@router.get("/{run_id}", response_model=ProductionRunRead)
def get_production_run(run_id: UUID, db: DbSession) -> ProductionRunRead:
    return production_run_service.get_run(db, run_id)


@router.post("/{run_id}/closeout", response_model=ProductionRunRead)
def closeout_production_run(run_id: UUID, payload: ProductionRunCloseout, db: DbSession) -> ProductionRunRead:
    return production_run_service.closeout_run(db, run_id, payload)
