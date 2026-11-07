from datetime import datetime

from pydantic import BaseModel


class NotificationItem(BaseModel):
    id: int
    kind: str
    athlete_id: int | None
    athlete_name: str | None
    ref_id: int | None
    sport: str | None
    is_read: bool
    created_at: datetime


class NotificationList(BaseModel):
    unread: int
    items: list[NotificationItem]
