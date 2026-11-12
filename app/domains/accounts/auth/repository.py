import json

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings

from app.domains.accounts.auth.queries import (
    CONSUME_PASSWORD_RESET,
    COUNT_RECENT_LOGIN_FAILURES,
    CREATE_SESSION,
    DELETE_SESSION,
    GET_PASSWORD_RESET,
    GET_SESSION_USER,
    GET_USER_FOR_LOGIN,
    RECORD_LOGIN_ATTEMPT,
    UPDATE_PASSWORD_HASH,
)


class AuthRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_user_for_login(self, email: str) -> dict | None:
        # None é un resultado válido aquí: o management iguala tempos e responde xenérico
        result = await self.db.execute(text(GET_USER_FOR_LOGIN), {"p_email": email})
        row = result.mappings().first()
        return dict(row) if row else None

    async def update_password_hash(self, user_id: int, password_hash: str) -> None:
        await self.db.execute(
            text(UPDATE_PASSWORD_HASH), {"p_user_id": user_id, "p_password_hash": password_hash}
        )
        await self.db.commit()

    async def record_login_attempt(self, email: str, ip: str | None, success: bool) -> None:
        await self.db.execute(
            text(RECORD_LOGIN_ATTEMPT), {"p_email": email, "p_ip": ip, "p_success": int(success)}
        )
        await self.db.commit()

    async def count_recent_failures(self, email: str, ip: str | None, minutes: int) -> dict:
        result = await self.db.execute(
            text(COUNT_RECENT_LOGIN_FAILURES), {"p_email": email, "p_ip": ip, "p_minutes": minutes}
        )
        return dict(result.mappings().first())

    async def create_session(
        self, token_hash: str, user_id: int, valid_days: int, ip: str | None, user_agent: str | None
    ) -> dict:
        result = await self.db.execute(
            text(CREATE_SESSION),
            {
                "p_token_hash": token_hash,
                "p_user_id": user_id,
                "p_valid_days": valid_days,
                "p_ip": ip,
                "p_user_agent": user_agent,
            },
        )
        row = result.mappings().first()
        await self.db.commit()
        if row is None:
            raise HTTPException(status_code=500, detail="session_error")
        return dict(row)

    async def get_session_user(self, token_hash: str) -> dict | None:
        result = await self.db.execute(text(GET_SESSION_USER), {"p_token_hash": token_hash})
        row = result.mappings().first()
        await self.db.commit()  # o procedemento actualiza last_seen_at
        if row is None:
            return None
        user = dict(row)
        user["roles"] = user["roles"].split(",") if user["roles"] else []
        user["athletes"] = json.loads(user["athletes"]) if user["athletes"] else []
        # Consentimentos sen responder ou dunha versión vella do texto: hai que volver pedilos
        version = get_settings().consent_version
        for a in user["athletes"]:
            a["training"] = bool(a.get("training"))
            a["consent_pending"] = a.get("consent_version") != version
        user["consents_pending"] = any(a["consent_pending"] for a in user["athletes"])
        return user

    async def delete_session(self, token_hash: str) -> None:
        await self.db.execute(text(DELETE_SESSION), {"p_token_hash": token_hash})
        await self.db.commit()

    async def get_password_reset(self, token_hash: str) -> dict:
        result = await self.db.execute(text(GET_PASSWORD_RESET), {"p_token_hash": token_hash})
        row = result.mappings().first()
        if row is None:
            raise HTTPException(status_code=404, detail="reset_not_found")
        data = dict(row)
        if data["status"] != "pending":
            raise HTTPException(status_code=410, detail=f"reset_{data['status']}")
        return data

    async def consume_password_reset(self, token_hash: str, password_hash: str) -> dict:
        result = await self.db.execute(
            text(CONSUME_PASSWORD_RESET), {"p_token_hash": token_hash, "p_password_hash": password_hash}
        )
        row = dict(result.mappings().first())
        if row["status"] != "ok":
            await self.db.rollback()
            raise HTTPException(status_code=410, detail="reset_invalid")
        await self.db.commit()
        return row
