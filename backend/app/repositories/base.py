"""
FinTwin AI — Generic Base Repository
Provides common CRUD operations using SQLAlchemy async sessions.
"""

from __future__ import annotations

from typing import Any, Generic, Type, TypeVar
from uuid import UUID

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.base import Base

ModelType = TypeVar("ModelType", bound=Base)


class BaseRepository(Generic[ModelType]):
    """Generic repository with standard CRUD operations."""

    def __init__(self, model: Type[ModelType], db: AsyncSession) -> None:
        self.model = model
        self.db = db

    async def get(self, id: UUID) -> ModelType | None:
        """Get a single record by primary key."""
        result = await self.db.execute(select(self.model).where(self.model.id == id))
        return result.scalar_one_or_none()

    async def get_by(self, **kwargs: Any) -> ModelType | None:
        """Get first record matching all kwargs as filters."""
        stmt = select(self.model)
        for field, value in kwargs.items():
            stmt = stmt.where(getattr(self.model, field) == value)
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def get_all(
        self,
        limit: int = 100,
        offset: int = 0,
        **kwargs: Any,
    ) -> list[ModelType]:
        """Get all records matching kwargs filters, paginated."""
        stmt = select(self.model)
        for field, value in kwargs.items():
            if value is not None:
                stmt = stmt.where(getattr(self.model, field) == value)
        stmt = stmt.limit(limit).offset(offset)
        result = await self.db.execute(stmt)
        return list(result.scalars().all())

    async def count(self, **kwargs: Any) -> int:
        """Count records matching kwargs filters."""
        stmt = select(func.count()).select_from(self.model)
        for field, value in kwargs.items():
            if value is not None:
                stmt = stmt.where(getattr(self.model, field) == value)
        result = await self.db.execute(stmt)
        return result.scalar_one()

    async def create(self, data: dict[str, Any]) -> ModelType:
        """Create a new record and return it."""
        instance = self.model(**data)
        self.db.add(instance)
        await self.db.flush()  # Get the ID without committing
        await self.db.refresh(instance)
        return instance

    async def update(self, id: UUID, data: dict[str, Any]) -> ModelType | None:
        """Update a record by ID with the provided fields."""
        # Remove None values to avoid overwriting with null
        clean_data = {k: v for k, v in data.items() if v is not None}
        if not clean_data:
            return await self.get(id)
        stmt = (
            update(self.model)
            .where(self.model.id == id)
            .values(**clean_data)
            .returning(self.model)
        )
        result = await self.db.execute(stmt)
        return result.scalar_one_or_none()

    async def delete(self, id: UUID) -> bool:
        """Hard delete a record. Use soft_delete for most entities."""
        instance = await self.get(id)
        if not instance:
            return False
        await self.db.delete(instance)
        return True

    async def bulk_create(self, data_list: list[dict[str, Any]]) -> list[ModelType]:
        """Bulk create multiple records efficiently."""
        instances = [self.model(**data) for data in data_list]
        self.db.add_all(instances)
        await self.db.flush()
        return instances
