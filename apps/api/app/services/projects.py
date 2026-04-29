from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Project
from app.schemas.common import PaginationParams
from app.schemas.projects import ProjectCreate, ProjectUpdate
from app.services.common import commit_and_refresh, delete_and_commit, get_or_404, paginate


def list_projects(db: Session, pagination: PaginationParams) -> tuple[list[Project], int]:
    stmt = select(Project).order_by(Project.created_at.desc(), Project.name.asc())
    return paginate(db, stmt, pagination)


def create_project(db: Session, payload: ProjectCreate) -> Project:
    project = Project(**payload.model_dump())
    db.add(project)
    return commit_and_refresh(db, project)


def get_project(db: Session, project_id: UUID | str) -> Project:
    return get_or_404(db, Project, project_id, "Project")


def update_project(db: Session, project_id: UUID | str, payload: ProjectUpdate) -> Project:
    project = get_project(db, project_id)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(project, key, value)
    return commit_and_refresh(db, project)


def delete_project(db: Session, project_id: UUID | str) -> Project:
    project = get_project(db, project_id)
    deleted_id = project.id
    delete_and_commit(db, project)
    project.id = deleted_id
    return project
