from dataclasses import dataclass

from fastapi import APIRouter, Depends

from app.core.auth import AuthContext, require_admin
from app.domains.accounts.users.management import UserManagement
from app.domains.accounts.users.repository import UserRepository
from app.domains.accounts.users.schemas import ResetLinkRequest, ResetLinkResponse, SetActiveRequest, UserListItem

router = APIRouter(prefix="/users", tags=["users"])


@dataclass
class AdminContext:
    user_id: int
    mgmt: UserManagement


async def get_admin_ctx(ctx: AuthContext = Depends(require_admin)) -> AdminContext:
    return AdminContext(user_id=ctx.user_id, mgmt=UserManagement(UserRepository(ctx.db)))


@router.get("/", response_model=list[UserListItem])
async def list_users(ctx: AdminContext = Depends(get_admin_ctx)):
    return await ctx.mgmt.list_all()


@router.post("/{user_id}/active", status_code=204)
async def set_user_active(user_id: int, body: SetActiveRequest, ctx: AdminContext = Depends(get_admin_ctx)):
    await ctx.mgmt.set_active(user_id, body.active, ctx.user_id)


@router.post("/{user_id}/reset-link", response_model=ResetLinkResponse)
async def create_reset_link(user_id: int, body: ResetLinkRequest, ctx: AdminContext = Depends(get_admin_ctx)):
    return await ctx.mgmt.create_reset_link(user_id, ctx.user_id, body.lang)
