from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.members.notifications.queries import LIST_NOTIFICATIONS, MARK_ALL_READ


class NotificationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_for_user(self, user_id: int, limit: int) -> list[dict]:
        result = await self.db.execute(text(LIST_NOTIFICATIONS), {"p_user_id": user_id, "p_limit": limit})
        return [{**dict(r), "is_read": bool(r["is_read"])} for r in result.mappings().all()]

    async def mark_all_read(self, user_id: int) -> int:
        result = await self.db.execute(text(MARK_ALL_READ), {"p_user_id": user_id})
        updated = result.mappings().first()["updated"]
        await self.db.commit()
        return updated
