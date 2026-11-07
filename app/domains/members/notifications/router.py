from dataclasses import dataclass

from fastapi import APIRouter, Depends, Query

from app.core.auth import AuthContext, get_auth_context
from app.domains.members.notifications.management import NotificationManagement
from app.domains.members.notifications.repository import NotificationRepository
from app.domains.members.notifications.schemas import NotificationList

router = APIRouter(prefix="/notifications", tags=["notifications"])


@dataclass
class Context:
    user_id: int
    mgmt: NotificationManagement


async def get_notification_ctx(ctx: AuthContext = Depends(get_auth_context)) -> Context:
    return Context(user_id=ctx.user_id, mgmt=NotificationManagement(NotificationRepository(ctx.db)))


@router.get("/", response_model=NotificationList)
async def list_notifications(limit: int = Query(default=30, ge=1, le=100), ctx: Context = Depends(get_notification_ctx)):
    return await ctx.mgmt.list_for_user(ctx.user_id, limit)


@router.post("/read", status_code=204)
async def mark_all_read(ctx: Context = Depends(get_notification_ctx)):
    await ctx.mgmt.mark_all_read(ctx.user_id)
