from __future__ import annotations
from datetime import datetime, timezone
from uuid import UUID
from sqlalchemy import and_, func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.exceptions import NotFoundError
from app.core.websocket_manager import ws_manager
from app.models.notification import Notification


class NotificationService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def create_notification(
        self,
        user_id: str,
        tenant_id: str,
        notification_type: str,
        title: str,
        body: str,
        action_url: str | None = None,
        metadata: dict | None = None,
    ) -> Notification:
        """Create and push real-time notification."""
        notif = Notification(
            user_id=UUID(user_id),
            tenant_id=UUID(tenant_id),
            type=notification_type,
            title=title,
            body=body,
            action_url=action_url,
            metadata=metadata or {},
        )
        self.db.add(notif)
        await self.db.flush()

        # Push real-time via WebSocket
        await ws_manager.send_to_user(
            user_id=user_id,
            message={
                "type": "notification",
                "data": {
                    "id": str(notif.id),
                    "title": title,
                    "body": body,
                    "notification_type": notification_type,
                    "action_url": action_url,
                },
            },
        )
        return notif

    async def list_notifications(
        self,
        user_id: str,
        is_read: bool | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> dict:
        conditions = [Notification.user_id == UUID(user_id)]
        if is_read is not None:
            conditions.append(Notification.is_read == is_read)

        where_clause = and_(*conditions)
        count_result = await self.db.execute(
            select(func.count()).select_from(Notification).where(where_clause)
        )
        items_result = await self.db.execute(
            select(Notification)
            .where(where_clause)
            .order_by(Notification.created_at.desc())
            .limit(limit)
            .offset(offset)
        )

        items = items_result.scalars().all()
        return {
            "items": [
                {
                    "id": str(n.id),
                    "type": n.type,
                    "title": n.title,
                    "body": n.body,
                    "action_url": n.action_url,
                    "is_read": n.is_read,
                    "created_at": n.created_at.isoformat(),
                }
                for n in items
            ],
            "total": count_result.scalar_one(),
            "unread_count": await self.get_unread_count(user_id),
        }

    async def mark_read(self, notification_id: UUID, user_id: str) -> None:
        result = await self.db.execute(
            select(Notification).where(
                and_(
                    Notification.id == notification_id,
                    Notification.user_id == UUID(user_id),
                )
            )
        )
        notif = result.scalar_one_or_none()
        if not notif:
            raise NotFoundError("Notification", str(notification_id))
        notif.is_read = True
        notif.read_at = datetime.now(timezone.utc)
        await self.db.flush()

    async def mark_all_read(self, user_id: str) -> None:
        await self.db.execute(
            update(Notification)
            .where(
                and_(
                    Notification.user_id == UUID(user_id),
                    Notification.is_read == False,
                )
            )
            .values(is_read=True, read_at=datetime.now(timezone.utc))
        )

    async def get_unread_count(self, user_id: str) -> int:
        result = await self.db.execute(
            select(func.count())
            .select_from(Notification)
            .where(
                and_(
                    Notification.user_id == UUID(user_id),
                    Notification.is_read == False,
                )
            )
        )
        return result.scalar_one()
