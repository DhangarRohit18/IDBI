from __future__ import annotations
from uuid import UUID
from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog


class AuditService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def list_logs(
        self,
        tenant_id: str,
        entity_type: str | None = None,
        action: str | None = None,
        user_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        conditions = [AuditLog.tenant_id == UUID(tenant_id)]
        if entity_type:
            conditions.append(AuditLog.entity_type == entity_type)
        if action:
            conditions.append(AuditLog.action == action)
        if user_id:
            conditions.append(AuditLog.user_id == UUID(user_id))

        where_clause = and_(*conditions)

        count_result = await self.db.execute(
            select(func.count()).select_from(AuditLog).where(where_clause)
        )
        total = count_result.scalar_one()

        items_result = await self.db.execute(
            select(AuditLog)
            .where(where_clause)
            .order_by(AuditLog.created_at.desc())
            .limit(limit)
            .offset(offset)
        )
        items = items_result.scalars().all()

        return {
            "items": [
                {
                    "id": str(log.id),
                    "entity_type": log.entity_type,
                    "entity_id": str(log.entity_id) if log.entity_id else None,
                    "action": log.action,
                    "user_id": str(log.user_id) if log.user_id else None,
                    "description": log.description,
                    "ip_address": log.ip_address,
                    "created_at": log.created_at.isoformat(),
                }
                for log in items
            ],
            "total": total,
            "limit": limit,
            "offset": offset,
        }
