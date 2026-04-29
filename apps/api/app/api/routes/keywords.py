from __future__ import annotations

from fastapi import APIRouter, status

from app.api.deps import DbSession
from app.schemas.keywords import KeywordCreate, KeywordDeleted, KeywordRead, KeywordUpdate
from app.services import keywords as keyword_service


router = APIRouter(tags=["keywords"])


@router.get("/api/projects/{project_id}/keywords", response_model=list[KeywordRead])
def list_project_keywords(project_id: str, db: DbSession) -> list[KeywordRead]:
    return keyword_service.list_project_keywords(db, project_id)


@router.post("/api/projects/{project_id}/keywords", response_model=KeywordRead, status_code=status.HTTP_201_CREATED)
def create_project_keyword(project_id: str, payload: KeywordCreate, db: DbSession) -> KeywordRead:
    return keyword_service.create_project_keyword(db, project_id, payload)


@router.put("/api/keywords/{keyword_id}", response_model=KeywordRead)
def update_keyword(keyword_id: str, payload: KeywordUpdate, db: DbSession) -> KeywordRead:
    return keyword_service.update_keyword(db, keyword_id, payload)


@router.delete("/api/keywords/{keyword_id}", response_model=KeywordDeleted)
def delete_keyword(keyword_id: str, db: DbSession) -> KeywordDeleted:
    deleted = keyword_service.delete_keyword(db, keyword_id)
    return KeywordDeleted(id=deleted.id)
