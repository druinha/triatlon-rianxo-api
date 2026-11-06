from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.accounts.invitations.queries import (
    ACCEPT_INVITATION_EXISTING_USER,
    ACCEPT_INVITATION_NEW_USER,
    CREATE_INVITATION,
    GET_INVITATION_BY_TOKEN,
    LIST_INVITATIONS,
    RENEW_INVITATION,
    REVOKE_INVITATION,
)


class InvitationRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self, token_hash: str, email: str, invited_name: str, kind: str, minor_name: str | None,
        is_athlete: bool, grant_admin: bool, grant_coach: bool, created_by: int | None, valid_days: int,
    ) -> dict:
        result = await self.db.execute(
            text(CREATE_INVITATION),
            {
                "p_token_hash": token_hash,
                "p_email": email,
                "p_invited_name": invited_name,
                "p_kind": kind,
                "p_minor_name": minor_name,
                "p_is_athlete": int(is_athlete),
                "p_grant_admin": int(grant_admin),
                "p_grant_coach": int(grant_coach),
                "p_created_by": created_by,
                "p_valid_days": valid_days,
            },
        )
        row = result.mappings().first()
        if row is None:
            raise HTTPException(status_code=500, detail="invitation_error")
        await self.db.commit()
        return dict(row)

    async def get_by_token(self, token_hash: str) -> dict:
        result = await self.db.execute(text(GET_INVITATION_BY_TOKEN), {"p_token_hash": token_hash})
        row = result.mappings().first()
        if row is None:
            raise HTTPException(status_code=404, detail="invitation_not_found")
        data = dict(row)
        if data["status"] != "pending":
            raise HTTPException(status_code=410, detail=f"invitation_{data['status']}")
        data["email_registered"] = bool(data["email_registered"])
        return data

    async def list_all(self) -> list[dict]:
        result = await self.db.execute(text(LIST_INVITATIONS))
        return [dict(r) for r in result.mappings().all()]

    async def revoke(self, invitation_id: int) -> dict:
        result = await self.db.execute(text(REVOKE_INVITATION), {"p_id": invitation_id})
        row = result.mappings().first()
        if row is None:
            raise HTTPException(status_code=404, detail="invitation_not_found")
        await self.db.commit()
        data = dict(row)
        if data["status"] == "used":
            raise HTTPException(status_code=409, detail="invitation_used")
        return data

    async def renew(self, invitation_id: int, token_hash: str, valid_days: int) -> dict:
        result = await self.db.execute(
            text(RENEW_INVITATION),
            {"p_id": invitation_id, "p_token_hash": token_hash, "p_valid_days": valid_days},
        )
        row = result.mappings().first()
        if row is None:
            raise HTTPException(status_code=404, detail="invitation_not_found")
        data = dict(row)
        if data["status"] != "renewed":
            await self.db.rollback()
            raise HTTPException(status_code=409, detail="invitation_used")
        await self.db.commit()
        return data

    async def accept_new_user(
        self, token_hash: str, password_hash: str, display_name: str | None, lang: str, consent_ver: str
    ) -> dict:
        result = await self.db.execute(
            text(ACCEPT_INVITATION_NEW_USER),
            {
                "p_token_hash": token_hash,
                "p_password_hash": password_hash,
                "p_display_name": display_name,
                "p_lang": lang,
                "p_consent_ver": consent_ver,
            },
        )
        data = dict(result.mappings().first())
        if data["status"] != "ok":
            await self.db.rollback()
            code = 409 if data["status"] == "email_taken" else 410
            raise HTTPException(status_code=code, detail=f"invitation_{data['status']}")
        await self.db.commit()
        return data

    async def accept_existing_user(self, token_hash: str, user_id: int) -> dict:
        result = await self.db.execute(
            text(ACCEPT_INVITATION_EXISTING_USER), {"p_token_hash": token_hash, "p_user_id": user_id}
        )
        data = dict(result.mappings().first())
        if data["status"] != "ok":
            await self.db.rollback()
            code = 403 if data["status"] == "wrong_user" else 410
            raise HTTPException(status_code=code, detail=f"invitation_{data['status']}")
        await self.db.commit()
        return data
