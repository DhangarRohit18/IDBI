from __future__ import annotations

from uuid import UUID
from datetime import datetime, timezone

from sqlalchemy import and_, func, or_, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.msme import MSME
from app.repositories.base import BaseRepository


class MSMERepository(BaseRepository[MSME]):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__(MSME, db)

    async def get_by_gstin(self, gstin: str, tenant_id: UUID) -> MSME | None:
        result = await self.db.execute(
            select(MSME).where(
                and_(MSME.gstin == gstin, MSME.tenant_id == tenant_id, MSME.deleted_at.is_(None))
            )
        )
        return result.scalar_one_or_none()

    async def search(
        self,
        tenant_id: UUID,
        query: str | None = None,
        industry_type: str | None = None,
        state: str | None = None,
        risk_tier: str | None = None,
        status: str | None = None,
        assigned_officer: UUID | None = None,
        limit: int = 25,
        offset: int = 0,
    ) -> tuple[list[MSME], int]:
        """Search MSMEs with filters. Returns (items, total_count)."""
        conditions = [
            MSME.tenant_id == tenant_id,
            MSME.deleted_at.is_(None),
        ]

        if query:
            conditions.append(
                or_(
                    MSME.business_name.ilike(f"%{query}%"),
                    MSME.gstin.ilike(f"%{query}%"),
                    MSME.pan.ilike(f"%{query}%"),
                )
            )
        if industry_type:
            conditions.append(MSME.industry_type == industry_type)
        if state:
            conditions.append(MSME.state == state)
        if risk_tier:
            conditions.append(MSME.risk_tier == risk_tier)
        if status:
            conditions.append(MSME.status == status)
        if assigned_officer:
            conditions.append(MSME.assigned_officer == assigned_officer)

        where_clause = and_(*conditions)

        count_result = await self.db.execute(
            select(func.count()).select_from(MSME).where(where_clause)
        )
        total = count_result.scalar_one()

        items_result = await self.db.execute(
            select(MSME)
            .where(where_clause)
            .order_by(MSME.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        items = list(items_result.scalars().all())

        return items, total

    async def soft_delete(self, msme_id: UUID, tenant_id: UUID) -> bool:
        """Soft-delete by setting deleted_at timestamp."""
        msme = await self.get(msme_id)
        if not msme or str(msme.tenant_id) != str(tenant_id):
            return False
        msme.deleted_at = datetime.now(timezone.utc)
        await self.db.flush()
        return True

    async def get_active_count(self, tenant_id: UUID) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(MSME)
            .where(
                and_(
                    MSME.tenant_id == tenant_id,
                    MSME.status == "ACTIVE",
                    MSME.deleted_at.is_(None),
                )
            )
        )
        return result.scalar_one()

    async def get_by_state(
        self, tenant_id: UUID, state: str
    ) -> list[MSME]:
        result = await self.db.execute(
            select(MSME).where(
                and_(
                    MSME.tenant_id == tenant_id,
                    MSME.state == state,
                    MSME.deleted_at.is_(None),
                )
            )
        )
        return list(result.scalars().all())

    async def get_high_risk(
        self, tenant_id: UUID, n: int = 10
    ) -> list[MSME]:
        result = await self.db.execute(
            select(MSME)
            .where(
                and_(
                    MSME.tenant_id == tenant_id,
                    MSME.risk_tier.in_(["HIGH", "VERY_HIGH"]),
                    MSME.deleted_at.is_(None),
                )
            )
            .order_by(MSME.latest_risk_score.desc())
            .limit(n)
        )
        return list(result.scalars().all())
