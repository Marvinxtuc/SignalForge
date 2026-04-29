from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import Keyword
from app.schemas.keywords import KeywordCreate, KeywordUpdate
from app.services.common import commit_and_refresh, delete_and_commit, get_or_404
from app.services.projects import get_project


def list_project_keywords(db: Session, project_id: UUID | str) -> list[Keyword]:
    project = get_project(db, project_id)
    stmt = (
        select(Keyword)
        .where(Keyword.project_id == project.id)
        .order_by(Keyword.keyword_type.asc(), Keyword.keyword.asc())
    )
    return list(db.scalars(stmt).all())


def create_project_keyword(db: Session, project_id: UUID | str, payload: KeywordCreate) -> Keyword:
    project = get_project(db, project_id)
    keyword = Keyword(project_id=project.id, **payload.model_dump())
    db.add(keyword)
    return commit_and_refresh(db, keyword)


def get_keyword(db: Session, keyword_id: UUID | str) -> Keyword:
    return get_or_404(db, Keyword, keyword_id, "Keyword")


def update_keyword(db: Session, keyword_id: UUID | str, payload: KeywordUpdate) -> Keyword:
    keyword = get_keyword(db, keyword_id)
    updates = payload.model_dump(exclude_unset=True)
    for key, value in updates.items():
        setattr(keyword, key, value)
    return commit_and_refresh(db, keyword)


def delete_keyword(db: Session, keyword_id: UUID | str) -> Keyword:
    keyword = get_keyword(db, keyword_id)
    deleted_id = keyword.id
    delete_and_commit(db, keyword)
    keyword.id = deleted_id
    return keyword
