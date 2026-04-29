from collections.abc import Iterable
from typing import Any, TypeVar
from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.errors import ApiError, conflict, not_found
from app.schemas.common import PaginatedResponse, PaginationParams


ModelT = TypeVar("ModelT")


def parse_uuid(value: str, field_name: str = "id") -> UUID:
    try:
        return UUID(str(value))
    except ValueError as exc:
        raise ApiError(
            code="validation_error",
            message=f"Invalid UUID for {field_name}",
            status_code=422,
            details={field_name: value},
        ) from exc


def get_or_404(db: Session, model: type[ModelT], object_id: UUID | str, label: str = "Resource") -> ModelT:
    parsed_id = object_id if isinstance(object_id, UUID) else parse_uuid(str(object_id))
    obj = db.get(model, parsed_id)
    if obj is None:
        raise not_found(f"{label} not found", {"id": str(parsed_id)})
    return obj


def paginate(db: Session, stmt: Select[Any], pagination: PaginationParams) -> tuple[list[Any], int]:
    total_stmt = select(func.count()).select_from(stmt.order_by(None).subquery())
    total = db.scalar(total_stmt) or 0
    items = list(db.scalars(stmt.offset(pagination.offset).limit(pagination.page_size)).all())
    return items, int(total)


def paginated_response(items: Iterable[Any], pagination: PaginationParams, total: int) -> PaginatedResponse[Any]:
    return PaginatedResponse(
        items=list(items),
        page=pagination.page,
        page_size=pagination.page_size,
        total=total,
    )


def commit_and_refresh(db: Session, obj: ModelT) -> ModelT:
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise conflict("Database constraint violation") from exc
    db.refresh(obj)
    return obj


def delete_and_commit(db: Session, obj: object) -> None:
    try:
        db.delete(obj)
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise conflict("Database constraint violation") from exc

