from fastapi import HTTPException

from app.core.config import get_settings
from app.core.security import new_token
from app.domains.accounts.users.repository import UserRepository

RESET_PATHS = {"gl": "/membros/restablecer/", "es": "/es/miembros/restablecer/"}


class UserManagement:
    def __init__(self, repository: UserRepository):
        self.database = repository
        self.settings = get_settings()

    async def list_all(self) -> list[dict]:
        return await self.database.list_all()

    async def set_active(self, user_id: int, active: bool, acting_user_id: int) -> dict:
        if user_id == acting_user_id and not active:
            raise HTTPException(status_code=400, detail="cannot_deactivate_self")
        return await self.database.set_active(user_id, active)

    async def create_reset_link(self, user_id: int, created_by: int, lang: str) -> dict:
        token, token_hash = new_token()
        row = await self.database.create_password_reset(token_hash, user_id, created_by, self.settings.reset_hours)
        link = f"{self.settings.site_url.rstrip('/')}{RESET_PATHS[lang]}#{token}"
        return {**row, "link": link}
