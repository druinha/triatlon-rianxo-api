import json
from datetime import date

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.members.athletes.queries import (
    GET_PHOTO,
    GET_PROFILE,
    LIST_DIRECTORY,
    SET_PHOTO,
    UPDATE_PROFILE,
)


def _sports(value: str | None) -> list[str]:
    return value.split(",") if value else []


def _raise_status(status: str) -> None:
    if status == "not_found":
        raise HTTPException(status_code=404, detail="athlete_not_found")
    if status == "forbidden":
        raise HTTPException(status_code=403, detail="profile_forbidden")
    if status != "ok":
        raise HTTPException(status_code=500, detail="generic")


class AthleteRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_profile(self, athlete_id: int, viewer_id: int) -> dict:
        result = await self.db.execute(
            text(GET_PROFILE), {"p_athlete_id": athlete_id, "p_viewer_id": viewer_id}
        )
        row = result.mappings().first()
        if row is None:
            raise HTTPException(status_code=404, detail="athlete_not_found")
        data = dict(row)
        data["sports"] = _sports(data["sports"])
        data["guardians"] = json.loads(data["guardians"]) if data["guardians"] else []
        data["can_edit"] = data["access"] == "manage"
        return data

    async def list_directory(self, viewer_id: int) -> list[dict]:
        result = await self.db.execute(text(LIST_DIRECTORY), {"p_viewer_id": viewer_id})
        items = []
        for r in result.mappings().all():
            item = dict(r)
            item["sports"] = _sports(item["sports"])
            items.append(item)
        return items

    async def update_profile(
        self,
        athlete_id: int,
        editor_id: int,
        first_name: str,
        last_name: str | None,
        nickname: str | None,
        birth_date: date | None,
        license_number: str | None,
        chip_code: str | None,
        sports: list[str],
    ) -> None:
        result = await self.db.execute(
            text(UPDATE_PROFILE),
            {
                "p_athlete_id": athlete_id,
                "p_editor_id": editor_id,
                "p_first_name": first_name,
                "p_last_name": last_name,
                "p_nickname": nickname,
                "p_birth_date": birth_date,
                "p_license": license_number,
                "p_chip": chip_code,
                "p_sports": json.dumps(sports),
            },
        )
        status = result.mappings().first()["status"]
        if status != "ok":
            await self.db.rollback()
            _raise_status(status)
        await self.db.commit()

    async def set_photo(self, athlete_id: int, editor_id: int, photo_file: str | None) -> str | None:
        """Garda a foto nova (ou None para quitala) e devolve o ficheiro anterior."""
        result = await self.db.execute(
            text(SET_PHOTO),
            {"p_athlete_id": athlete_id, "p_editor_id": editor_id, "p_photo_file": photo_file},
        )
        row = dict(result.mappings().first())
        if row["status"] != "ok":
            await self.db.rollback()
            _raise_status(row["status"])
        await self.db.commit()
        return row["old_photo_file"]

    async def get_photo(self, athlete_id: int, viewer_id: int) -> str:
        result = await self.db.execute(
            text(GET_PHOTO), {"p_athlete_id": athlete_id, "p_viewer_id": viewer_id}
        )
        row = result.mappings().first()
        if row is None:
            raise HTTPException(status_code=404, detail="photo_not_found")
        return row["photo_file"]
