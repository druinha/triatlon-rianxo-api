from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.members.consents.queries import HAS_TRAINING, LIST_MINE, LIST_STAFF, SET_CONSENT

_BOOLS = ("is_minor", "training", "img_web", "img_social", "img_whatsapp", "img_print")


def _row(r) -> dict:
    d = dict(r)
    for k in _BOOLS:
        if d.get(k) is not None:
            d[k] = bool(d[k])
    return d


class ConsentRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_mine(self, user_id: int) -> list[dict]:
        result = await self.db.execute(text(LIST_MINE), {"p_user_id": user_id})
        return [_row(r) for r in result.mappings().all()]

    async def list_staff(self, viewer_id: int) -> list[dict]:
        result = await self.db.execute(text(LIST_STAFF), {"p_viewer_id": viewer_id})
        return [_row(r) for r in result.mappings().all()] if result.returns_rows else []

    async def set(self, athlete_id: int, user_id: int, values: dict, version: str,
                  ip: str | None, ua: str | None) -> bool:
        result = await self.db.execute(
            text(SET_CONSENT),
            {
                "p_athlete_id": athlete_id,
                "p_user_id": user_id,
                "p_training": int(values["training"]),
                "p_web": int(values["img_web"]),
                "p_social": int(values["img_social"]),
                "p_whatsapp": int(values["img_whatsapp"]),
                "p_print": int(values["img_print"]),
                "p_version": version,
                "p_ip": ip,
                "p_ua": ua,
            },
        )
        row = result.mappings().first()
        if row["status"] != "ok":
            await self.db.rollback()
            if row["status"] == "forbidden":
                raise HTTPException(status_code=403, detail="consent_forbidden")
            raise HTTPException(status_code=500, detail="generic")
        await self.db.commit()
        return bool(row["wiped"])

    async def has_training(self, athlete_id: int) -> bool:
        result = await self.db.execute(text(HAS_TRAINING), {"p_athlete_id": athlete_id})
        return bool(result.mappings().first()["ok"])
