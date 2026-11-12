from fastapi import HTTPException

from app.core.config import get_settings
from app.domains.members.consents.repository import ConsentRepository
from app.domains.members.consents.schemas import ConsentIn


class ConsentManagement:
    def __init__(self, repository: ConsentRepository):
        self.database = repository
        self.version = get_settings().consent_version

    def _mark(self, rows: list[dict]) -> list[dict]:
        for r in rows:
            r["pending"] = r.get("version") != self.version
        return rows

    async def list_mine(self, user_id: int) -> list[dict]:
        return self._mark(await self.database.list_mine(user_id))

    async def list_staff(self, viewer_id: int) -> list[dict]:
        return self._mark(await self.database.list_staff(viewer_id))

    async def set(self, athlete_id: int, user_id: int, body: ConsentIn, ip: str | None, ua: str | None) -> dict:
        wiped = await self.database.set(athlete_id, user_id, body.model_dump(), self.version, ip, ua)
        row = next(r for r in await self.list_mine(user_id) if r["athlete_id"] == athlete_id)
        return {"wiped": wiped, "row": row}

    async def require_training(self, athlete_id: int) -> None:
        """Sen consentimento de adestramento non se gardan tests nin sesións."""
        if not await self.database.has_training(athlete_id):
            raise HTTPException(status_code=403, detail="training_consent_required")
