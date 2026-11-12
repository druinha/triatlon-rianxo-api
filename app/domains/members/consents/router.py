from dataclasses import dataclass

from fastapi import APIRouter, Depends, Request

from app.core.auth import AuthContext, client_ip, get_auth_context, require_coach, user_agent
from app.domains.members.consents.management import ConsentManagement
from app.domains.members.consents.repository import ConsentRepository
from app.domains.members.consents.schemas import ConsentIn, ConsentRow, ConsentSaved

router = APIRouter(prefix="/consents", tags=["consents"])


@dataclass
class Context:
    user_id: int
    mgmt: ConsentManagement


async def get_consent_ctx(ctx: AuthContext = Depends(get_auth_context)) -> Context:
    return Context(user_id=ctx.user_id, mgmt=ConsentManagement(ConsentRepository(ctx.db)))


async def get_staff_ctx(ctx: AuthContext = Depends(require_coach)) -> Context:
    return Context(user_id=ctx.user_id, mgmt=ConsentManagement(ConsentRepository(ctx.db)))


@router.get("/mine", response_model=list[ConsentRow])
async def mine(ctx: Context = Depends(get_consent_ctx)):
    return await ctx.mgmt.list_mine(ctx.user_id)


@router.get("/staff", response_model=list[ConsentRow])
async def staff(ctx: Context = Depends(get_staff_ctx)):
    return await ctx.mgmt.list_staff(ctx.user_id)


@router.post("/{athlete_id}", response_model=ConsentSaved)
async def set_consent(athlete_id: int, body: ConsentIn, request: Request, ctx: Context = Depends(get_consent_ctx)):
    return await ctx.mgmt.set(athlete_id, ctx.user_id, body, client_ip(request), user_agent(request))
