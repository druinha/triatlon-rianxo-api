from fastapi import HTTPException

from app.core.config import get_settings
from app.core.security import hash_password, hash_token, new_token
from app.domains.accounts.auth.management import AuthManagement, NewSession
from app.domains.accounts.invitations.repository import InvitationRepository

# Páxinas da web onde se abre a ligazón (o token vai despois do #, así nunca chega a ningún servidor)
INVITE_PATHS = {"gl": "/membros/invitacion/", "es": "/es/miembros/invitacion/"}


class InvitationManagement:
    def __init__(self, repository: InvitationRepository, auth: AuthManagement):
        self.database = repository
        self.auth = auth
        self.settings = get_settings()

    def _link(self, token: str, lang: str) -> str:
        return f"{self.settings.site_url.rstrip('/')}{INVITE_PATHS[lang]}#{token}"

    async def create(self, data, created_by: int | None) -> dict:
        token, token_hash = new_token()
        row = await self.database.create(
            token_hash, data.email, data.invited_name, data.kind, data.minor_name,
            data.is_athlete, data.grant_admin, data.grant_coach, created_by,
            self.settings.invitation_days,
        )
        return {**row, "link": self._link(token, data.lang)}

    async def list_all(self) -> list[dict]:
        return await self.database.list_all()

    async def revoke(self, invitation_id: int) -> dict:
        return await self.database.revoke(invitation_id)

    async def renew(self, invitation_id: int, lang: str) -> dict:
        token, token_hash = new_token()
        row = await self.database.renew(invitation_id, token_hash, self.settings.invitation_days)
        return {**row, "link": self._link(token, lang)}

    async def get_info(self, token: str) -> dict:
        return await self.database.get_by_token(hash_token(token))

    async def accept(self, body, ip: str | None, user_agent: str | None) -> NewSession:
        token_hash = hash_token(body.token)
        invitation = await self.database.get_by_token(token_hash)

        if invitation["email_registered"]:
            # Conta existente (p. ex. un pai co segundo fillo): confirma co seu contrasinal actual
            user = await self.auth.verify_credentials(invitation["email"], body.password, ip)
            await self.database.accept_existing_user(token_hash, user["id"])
            user_id = user["id"]
        else:
            if not body.consent:
                raise HTTPException(status_code=422, detail="consent_required")
            self.auth.validate_new_password(body.password)
            row = await self.database.accept_new_user(
                token_hash, hash_password(body.password), body.display_name, body.lang,
                self.settings.consent_version,
            )
            user_id = row["user_id"]

        return await self.auth.start_session(user_id, ip, user_agent)
