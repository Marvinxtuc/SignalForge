from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import DbSession, PaginationDep
from app.schemas.common import PaginatedResponse
from app.schemas.projects import ProjectCreate, ProjectDeleted, ProjectRead, ProjectUpdate
from app.services import projects as project_service
from app.services.common import paginated_response


router = APIRouter(prefix="/api/projects", tags=["projects"])


@router.get("", response_model=PaginatedResponse[ProjectRead])
def list_projects(db: DbSession, pagination: PaginationDep) -> PaginatedResponse[ProjectRead]:
    projects, total = project_service.list_projects(db, pagination)
    return paginated_response(projects, pagination, total)


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(payload: ProjectCreate, db: DbSession) -> ProjectRead:
    return project_service.create_project(db, payload)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: str, db: DbSession) -> ProjectRead:
    return project_service.get_project(db, project_id)


@router.put("/{project_id}", response_model=ProjectRead)
def update_project(project_id: str, payload: ProjectUpdate, db: DbSession) -> ProjectRead:
    return project_service.update_project(db, project_id, payload)


@router.delete("/{project_id}", response_model=ProjectDeleted)
def delete_project(project_id: str, db: DbSession) -> ProjectDeleted:
    deleted = project_service.delete_project(db, project_id)
    return ProjectDeleted(id=deleted.id)
