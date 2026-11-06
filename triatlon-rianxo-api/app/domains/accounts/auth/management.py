from dataclasses import dataclass
from datetime import datetime

from fastapi import HTTPException

from app.core.config import get_settings
from app.core.security import hash_password, hash_token, needs_rehash, new_token, verify_password
from app.domains.accounts.auth.repository import AuthRepository


@dataclass
class NewSession:
    token: str
    expires_at: datetime
    user_id: int


class AuthManagement:
    def __init__(self, repository: AuthRepository):
        self.database = repository
        self.settings = get_settings()

    def validate_new_password(self, password: str) -> None:
        if len(password) < self.settings.password_min_length:
            raise HTTPException(status_code=422, detail="password_too_short")

    async def check_rate_limit(self, email: str, ip: str | None) -> None:
        counts = await self.database.count_recent_failures(email, ip, self.settings.login_window_minutes)
        if (
            counts["email_failures"] >= self.settings.login_max_email_failures
            or counts["ip_failures"] >= self.settings.login_max_ip_failures
        ):
            raise HTTPException(status_code=429, detail="too_many_attempts")

    async def verify_credentials(self, email: str, password: str, ip: str | None) -> dict:
        """Comproba email+contrasinal con límite de intentos. Devolve a conta."""
        await self.check_rate_limit(email, ip)
        user = await self.database.get_user_for_login(email)
        ok = verify_password(user["password_hash"] if user else None, password)
        await self.database.record_login_attempt(email, ip, ok)
        if not ok or user is None:
            raise HTTPException(status_code=401, detail="invalid_credentials")
        if not user["is_active"]:
            raise HTTPException(status_code=403, detail="account_disabled")
        if needs_rehash(user["password_hash"]):
            await self.database.update_password_hash(user["id"], hash_password(password))
        return user

    async def start_session(self, user_id: int, ip: str | None, user_agent: str | None) -> NewSession:
        token, token_hash = new_token()
        row = await self.database.create_session(
            token_hash, user_id, self.settings.session_days, ip, user_agent
        )
        return NewSession(token=token, expires_at=row["expires_at"], user_id=user_id)

    async def login(self, email: str, password: str, ip: str | None, user_agent: str | None) -> NewSession:
        user = await self.verify_credentials(email, password, ip)
        return await self.start_session(user["id"], ip, user_agent)

    async def get_session_user(self, token: str) -> dict | None:
        return await self.database.get_session_user(hash_token(token))

    async def logout(self, token: str) -> None:
        await self.database.delete_session(hash_token(token))

    async def get_password_reset(self, token: str) -> dict:
        return await self.database.get_password_reset(hash_token(token))

    async def complete_password_reset(
        self, token: str, password: str, ip: str | None, user_agent: str | None
    ) -> NewSession:
        self.validate_new_password(password)
        row = await self.database.consume_password_reset(hash_token(token), hash_password(password))
        return await self.start_session(row["user_id"], ip, user_agent)
