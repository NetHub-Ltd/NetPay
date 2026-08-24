from __future__ import annotations

from typing import Any, Dict, Generic, List, Optional, Sequence, Tuple, Type, TypeVar
from uuid import UUID

from fastapi import HTTPException, status
from loguru import logger
from pydantic import BaseModel, TypeAdapter, ValidationError
from sqlalchemy import or_
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlmodel import SQLModel, col, func, select
from sqlmodel.ext.asyncio.session import AsyncSession

ModelType = TypeVar("ModelType", bound=SQLModel)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseCRUD(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    async def get(self, db: AsyncSession, id: UUID) -> Optional[ModelType]:
        """Fetch a single record by primary UUID key."""
        try:
            stmt = select(self.model).where(col(self.model.id) == id)
            result = await db.exec(stmt)
            return result.one_or_none()
        except SQLAlchemyError as e:
            logger.error("Database read error during get() on {}: {}", self.model.__name__, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database retrieval operation failed.",
            )

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
    ) -> Sequence[ModelType]:
        """Retrieve multiple records, latest-first via created_at (fallback id)."""
        try:
            stmt = select(self.model)
            if hasattr(self.model, "created_at"):
                stmt = stmt.order_by(col(self.model.created_at).desc())
            else:
                stmt = stmt.order_by(col(self.model.id).desc())
            stmt = stmt.offset(skip).limit(limit)
            result = await db.exec(stmt)
            return result.all()
        except SQLAlchemyError as e:
            logger.error("Database read error during get_multi() on {}: {}", self.model.__name__, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database batch retrieval operation failed.",
            )

    async def get_multi_paginated(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        where_clauses: Optional[List[Any]] = None,
        sort_by: Optional[str] = None,
        sort_order: str = "desc",
    ) -> Tuple[Sequence[ModelType], int]:
        """Return a window of records plus total count matching filters."""
        try:
            data_stmt = select(self.model)
            count_stmt = select(func.count()).select_from(self.model)

            if where_clauses:
                for clause in where_clauses:
                    data_stmt = data_stmt.where(clause)
                    count_stmt = count_stmt.where(clause)

            sort_column = None
            if sort_by and sort_by in self.model.__mapper__.columns:
                sort_column = col(getattr(self.model, sort_by))
            elif hasattr(self.model, "created_at"):
                sort_column = col(getattr(self.model, "created_at"))
            elif hasattr(self.model, "id"):
                sort_column = col(getattr(self.model, "id"))

            if sort_column is not None:
                if sort_order.lower() == "asc":
                    data_stmt = data_stmt.order_by(sort_column.asc())
                else:
                    data_stmt = data_stmt.order_by(sort_column.desc())

            data_stmt = data_stmt.offset(skip).limit(limit)

            count_result = await db.exec(count_stmt)
            total = count_result.one()
            data_result = await db.exec(data_stmt)
            items = data_result.all()
            return items, total
        except SQLAlchemyError as e:
            logger.error(
                "Database read error during get_multi_paginated() on {}: {}",
                self.model.__name__,
                str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database paginated batch retrieval operation failed.",
            )

    async def get_by_attributes(
        self,
        db: AsyncSession,
        *,
        filters: Dict[str, Any],
        skip: int = 0,
        limit: int = 100,
        descending: bool = False,
        sort_field: Optional[str] = None,
    ) -> Sequence[ModelType]:
        """Exact-match filter with optional runtime field validation."""
        try:
            stmt = select(self.model)
            for field_name, value in filters.items():
                if not hasattr(self.model, field_name):
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Field '{field_name}' invalid for model {self.model.__name__}",
                    )
                field_info = getattr(self.model, "model_fields", {}).get(field_name)
                if field_info and value is not None:
                    try:
                        TypeAdapter(field_info.annotation).validate_python(value)
                    except ValidationError:
                        raise HTTPException(
                            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail=f"Value '{value}' is invalid for field '{field_name}'",
                        )
                stmt = stmt.where(getattr(self.model, field_name) == value)

            target_sort = sort_field if sort_field and hasattr(self.model, sort_field) else "id"
            if descending:
                stmt = stmt.order_by(col(getattr(self.model, target_sort)).desc())
            else:
                stmt = stmt.order_by(col(getattr(self.model, target_sort)).asc())

            result = await db.exec(stmt.offset(skip).limit(limit))
            return result.all()
        except HTTPException:
            raise
        except SQLAlchemyError as e:
            logger.error(
                "Database error during get_by_attributes() on {}: {}",
                self.model.__name__,
                str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Attribute filter execution failed internally.",
            )

    async def search(
        self,
        db: AsyncSession,
        *,
        search_query: str,
        search_fields: List[str],
        filters: Optional[Dict[str, Any]] = None,
        skip: int = 0,
        limit: int = 100,
        order_by: str = "created_at",
        descending: bool = True,
    ) -> Tuple[Sequence[ModelType], int]:
        """Paginated ILIKE search across fields with optional exact filters."""
        try:
            if not search_query.strip():
                records = await self.get_multi(db, skip=skip, limit=limit)
                total_stmt = select(func.count()).select_from(self.model)
                total_res = await db.exec(total_stmt)
                return records, (total_res.one() or 0)

            base_stmt = select(self.model)

            if filters:
                for field_name, value in filters.items():
                    if hasattr(self.model, field_name) and value is not None:
                        base_stmt = base_stmt.where(getattr(self.model, field_name) == value)

            search_conditions = []
            for field in search_fields:
                if hasattr(self.model, field):
                    search_conditions.append(col(getattr(self.model, field)).ilike(f"%{search_query}%"))
            if search_conditions:
                base_stmt = base_stmt.where(or_(*search_conditions))

            count_stmt = select(func.count()).select_from(base_stmt.subquery())
            count_result = await db.exec(count_stmt)
            total_count = count_result.one() or 0

            sort_attr = getattr(self.model, order_by) if hasattr(self.model, order_by) else self.model.id
            if descending:
                base_stmt = base_stmt.order_by(col(sort_attr).desc())
            else:
                base_stmt = base_stmt.order_by(col(sort_attr).asc())

            final_stmt = base_stmt.offset(skip).limit(limit)
            records_result = await db.exec(final_stmt)
            return records_result.all(), total_count
        except SQLAlchemyError as e:
            logger.error("Global search failed on model {}: {}", self.model.__name__, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Generic search routine encountered a persistent error.",
            )

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType | Dict[str, Any]) -> ModelType:
        """Validate/build model and flush (caller commits)."""
        if isinstance(obj_in, BaseModel):
            obj_data = obj_in.model_dump()
        else:
            obj_data = obj_in
        db_obj = self.model(**obj_data)
        try:
            db.add(db_obj)
            await db.flush()
            await db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            await db.rollback()
            logger.error(
                "Integrity Constraint Violation during create on {}: {}",
                self.model.__name__,
                str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Resource conflict occurred: uniqueness or relationship constraint violated.",
            )
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error("Transaction rollback during create on {}: {}", self.model.__name__, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database transaction write failure.",
            )

    async def update(
        self,
        db: AsyncSession,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | Dict[str, Any],
    ) -> ModelType:
        """Partial update on an existing tracked instance (caller commits)."""
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            if hasattr(db_obj, field):
                setattr(db_obj, field, value)
        db.add(db_obj)
        try:
            await db.flush()
            await db.refresh(db_obj)
            return db_obj
        except IntegrityError as e:
            await db.rollback()
            logger.error(
                "Integrity Constraint Violation during update on {}: {}",
                self.model.__name__,
                str(e),
            )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Modification breaks unique data rules or constraints.",
            )
        except SQLAlchemyError as e:
            await db.rollback()
            logger.error("Transaction rollback during update on {}: {}", self.model.__name__, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database write persistence failure during modification.",
            )

    async def remove(self, db: AsyncSession, *, id: UUID) -> Optional[ModelType]:
        """Delete by primary key (caller commits)."""
        obj = await self.get(db, id)
        if obj:
            try:
                await db.delete(obj)
                await db.flush()
            except SQLAlchemyError as e:
                await db.rollback()
                logger.error(
                    "Transaction rollback during deletion on {}: {}",
                    self.model.__name__,
                    str(e),
                )
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database entity removal operation failed.",
                )
        return obj

    async def count(self, db: AsyncSession, *, where_clauses: Optional[List[Any]] = None) -> int:
        """Count rows, optionally filtered."""
        try:
            stmt = select(func.count()).select_from(self.model)
            if where_clauses:
                for clause in where_clauses:
                    stmt = stmt.where(clause)
            result = await db.exec(stmt)
            return int(result.one() or 0)
        except SQLAlchemyError as e:
            logger.error("Database count error on {}: {}", self.model.__name__, str(e))
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Internal database count operation failed.",
            )
