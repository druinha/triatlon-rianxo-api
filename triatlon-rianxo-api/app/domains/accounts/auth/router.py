from dataclasses import dataclass

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import (
    AuthContext,
    clear_session_cookie,
    client_ip,
    get_auth_context,
    get_public_db,
    set_session_cookie,
    user_agent,
)
from app.domains.accounts.auth.management import AuthManagement
from app.domains.accounts.auth.repository import AuthRepository
from app.domains.accounts.auth.schemas import (
    LoginRequest,
    MeResponse,
    ResetCompleteRequest,
    ResetInfoResponse,
    TokenRequest,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@dataclass
class PublicContext:
    mgmt: AuthManagement


@dataclass
class Context:
    user_id: int
    session_token: str
    user: dict
    mgmt: AuthManagement


async def get_public_auth_ctx(db: AsyncSession = Depends(get_public_db)) -> PublicContext:
    return PublicContext(mgmt=AuthManagement(AuthRepository(db)))


async def get_auth_ctx(ctx: AuthContext = Depends(get_auth_context)) -> Context:
    return Context(
        user_id=ctx.user_id,
        session_token=ctx.session_token,
        user=ctx.user,
        mgmt=AuthManagement(AuthRepository(ctx.db)),
    )


@router.post("/login", status_code=204)
async def login(body: LoginRequest, request: Request, response: Response,
                ctx: PublicContext = Depends(get_public_auth_ctx)):
    session = await ctx.mgmt.login(body.email, body.password, client_ip(request), user_agent(request))
    set_session_cookie(response, session.token, session.expires_at)


@router.post("/logout", status_code=204)
async def logout(response: Response, ctx: Context = Depends(get_auth_ctx)):
    await ctx.mgmt.logout(ctx.session_token)
    clear_session_cookie(response)


@router.get("/me", response_model=MeResponse)
async def me(ctx: Context = Depends(get_auth_ctx)):
    return ctx.user


@router.post("/reset/check", response_model=ResetInfoResponse)
async def check_reset(body: TokenRequest, ctx: PublicContext = Depends(get_public_auth_ctx)):
    return await ctx.mgmt.get_password_reset(body.token)


@router.post("/reset/complete", status_code=204)
async def complete_reset(body: ResetCompleteRequest, request: Request, response: Response,
                         ctx: PublicContext = Depends(get_public_auth_ctx)):
    session = await ctx.mgmt.complete_password_reset(
        body.token, body.password, client_ip(request), user_agent(request)
    )
    set_session_cookie(response, session.token, session.expires_at)
