from app.domains.members.notifications.repository import NotificationRepository


class NotificationManagement:
    def __init__(self, repository: NotificationRepository):
        self.database = repository

    async def list_for_user(self, user_id: int, limit: int) -> dict:
        items = await self.database.list_for_user(user_id, limit)
        return {"unread": sum(not i["is_read"] for i in items), "items": items}

    async def mark_all_read(self, user_id: int) -> None:
        await self.database.mark_all_read(user_id)
