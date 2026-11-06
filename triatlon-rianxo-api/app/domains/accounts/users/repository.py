import json

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.accounts.users.queries import CREATE_PASSWORD_RESET, LIST_USERS, SET_USER_ACTIVE


class UserRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_all(self) -> list[dict]:
        result = await self.db.execute(text(LIST_USERS))
        users = []
        for r in result.mappings().all():
            u = dict(r)
            u["roles"] = u["roles"].split(",") if u["roles"] else []
            u["minors"] = json.loads(u["minors"]) if u["minors"] else []
            users.append(u)
        return users

    async def set_active(self, user_id: int, active: bool) -> dict:
        result = await self.db.execute(text(SET_USER_ACTIVE), {"p_user_id": user_id, "p_active": int(active)})
        data = dict(result.mappings().first())
        if data["status"] == "not_found":
            raise HTTPException(status_code=404, detail="user_not_found")
        if data["status"] == "last_admin":
            raise HTTPException(status_code=409, detail="last_admin")
        await self.db.commit()
        return data

    async def create_password_reset(self, token_hash: str, user_id: int, created_by: int, valid_hours: int) -> dict:
        result = await self.db.execute(
            text(CREATE_PASSWORD_RESET),
            {"p_token_hash": token_hash, "p_user_id": user_id, "p_created_by": created_by, "p_valid_hours": valid_hours},
        )
        data = dict(result.mappings().first())
        if data["status"] != "ok":
            raise HTTPException(status_code=404, detail="user_not_found")
        await self.db.commit()
        return data
