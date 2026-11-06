from dataclasses import dataclass

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthContext, client_ip, get_public_db, require_admin, set_session_cookie, user_agent
from app.domains.accounts.auth.management import AuthManagement
from app.domains.accounts.auth.repository import AuthRepository
from app.domains.accounts.invitations.management import InvitationManagement
from app.domains.accounts.invitations.repository import InvitationRepository
from app.domains.accounts.invitations.schemas import (
    InvitationAccept,
    InvitationCheck,
    InvitationCreate,
    InvitationInfo,
    InvitationLink,
    InvitationListItem,
    InvitationRenew,
    InvitationStatus,
)

router = APIRouter(prefix="/invitations", tags=["invitations"])


@dataclass
class PublicContext:
    mgmt: InvitationManagement


@dataclass
class AdminContext:
    user_id: int
    mgmt: InvitationManagement


def _mgmt(db: AsyncSession) -> InvitationManagement:
    return InvitationManagement(InvitationRepository(db), AuthManagement(AuthRepository(db)))


async def get_public_ctx(db: AsyncSession = Depends(get_public_db)) -> PublicContext:
    return PublicContext(mgmt=_mgmt(db))


async def get_admin_ctx(ctx: AuthContext = Depends(require_admin)) -> AdminContext:
    return AdminContext(user_id=ctx.user_id, mgmt=_mgmt(ctx.db))


# ── Público (a persoa invitada) ──

@router.post("/check", response_model=InvitationInfo)
async def check_invitation(body: InvitationCheck, ctx: PublicContext = Depends(get_public_ctx)):
    return await ctx.mgmt.get_info(body.token)


@router.post("/accept", status_code=204)
async def accept_invitation(body: InvitationAccept, request: Request, response: Response,
                            ctx: PublicContext = Depends(get_public_ctx)):
    session = await ctx.mgmt.accept(body, client_ip(request), user_agent(request))
    set_session_cookie(response, session.token, session.expires_at)


# ── Admin ──

@router.get("/", response_model=list[InvitationListItem])
async def list_invitations(ctx: AdminContext = Depends(get_admin_ctx)):
    return await ctx.mgmt.list_all()


@router.post("/", response_model=InvitationLink, status_code=201)
async def create_invitation(body: InvitationCreate, ctx: AdminContext = Depends(get_admin_ctx)):
    return await ctx.mgmt.create(body, ctx.user_id)


@router.post("/{invitation_id}/revoke", response_model=InvitationStatus)
async def revoke_invitation(invitation_id: int, ctx: AdminContext = Depends(get_admin_ctx)):
    return await ctx.mgmt.revoke(invitation_id)


@router.post("/{invitation_id}/renew", response_model=InvitationLink)
async def renew_invitation(invitation_id: int, body: InvitationRenew, ctx: AdminContext = Depends(get_admin_ctx)):
    return await ctx.mgmt.renew(invitation_id, body.lang)
