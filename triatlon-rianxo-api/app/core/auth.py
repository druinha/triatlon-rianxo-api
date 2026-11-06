from dataclasses import dataclass, field
from datetime import datetime, timezone

from fastapi import Depends, HTTPException, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.db import get_db
from app.core.security import hash_token
from app.domains.accounts.auth.repository import AuthRepository


@dataclass
class AuthContext:
    db: AsyncSession
    user_id: int
    user: dict
    roles: set[str] = field(default_factory=set)
    session_token: str = ""


def client_ip(request: Request) -> str | None:
    # Uvicorn arrancado con --proxy-headers detrás de Caddy xa pon aquí a IP real
    return request.client.host if request.client else None


def user_agent(request: Request) -> str | None:
    return request.headers.get("user-agent")


async def get_public_db(db: AsyncSession = Depends(get_db)) -> AsyncSession:
    return db


async def get_auth_context(request: Request, db: AsyncSession = Depends(get_db)) -> AuthContext:
    token = request.cookies.get(get_settings().cookie_name)
    if not token:
        raise HTTPException(status_code=401, detail="not_authenticated")
    user = await AuthRepository(db).get_session_user(hash_token(token))
    if user is None:
        raise HTTPException(status_code=401, detail="not_authenticated")
    return AuthContext(
        db=db, user_id=user["user_id"], user=user, roles=set(user["roles"]), session_token=token
    )


async def require_admin(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
    if "admin" not in ctx.roles:
        raise HTTPException(status_code=403, detail="admin_required")
    return ctx


async def require_coach(ctx: AuthContext = Depends(get_auth_context)) -> AuthContext:
    if not ctx.roles & {"coach", "admin"}:
        raise HTTPException(status_code=403, detail="coach_required")
    return ctx


def set_session_cookie(response: Response, token: str, expires_at: datetime) -> None:
    s = get_settings()
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    response.set_cookie(
        key=s.cookie_name,
        value=token,
        expires=expires_at,
        httponly=True,
        secure=s.cookie_secure,
        samesite="lax",
        path="/",
    )


def clear_session_cookie(response: Response) -> None:
    s = get_settings()
    response.delete_cookie(key=s.cookie_name, path="/", secure=s.cookie_secure, httponly=True, samesite="lax")
