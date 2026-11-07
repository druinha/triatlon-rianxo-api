import json
from datetime import date, timedelta

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.members.races.queries import (
    CREATE_RACE,
    DELETE_RACE,
    FIND_SIMILAR,
    GET_ATTENDEES,
    GET_RACE,
    LIST_FOR_ATHLETE,
    LIST_RACES,
    PUBLIC_LIST,
    SET_ATTENDANCE,
    UPDATE_RACE,
)


def _hhmm(value) -> str | None:
    """aiomysql devolve as columnas TIME como timedelta."""
    if value is None:
        return None
    if isinstance(value, timedelta):
        minutes = int(value.total_seconds()) // 60
        return f"{minutes // 60:02d}:{minutes % 60:02d}"
    return str(value)[:5]


def _race_row(row) -> dict:
    data = dict(row)
    if "start_time" in data:
        data["start_time"] = _hhmm(data["start_time"])
    for key in ("can_edit", "is_past", "registered", "is_minor", "is_mine"):
        if key in data:
            data[key] = bool(data[key])
    for key in ("who", "mine"):
        if key in data:
            data[key] = json.loads(data[key]) if data[key] else []
    return data


def _raise_status(status: str) -> None:
    if status == "not_found":
        raise HTTPException(status_code=404, detail="race_not_found")
    if status == "forbidden":
        raise HTTPException(status_code=403, detail="race_forbidden")
    if status != "ok":
        raise HTTPException(status_code=500, detail="generic")


class RaceRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_races(self, viewer_id: int, only_mine: bool) -> list[dict]:
        result = await self.db.execute(
            text(LIST_RACES), {"p_viewer_id": viewer_id, "p_only_mine": int(only_mine)}
        )
        return [_race_row(r) for r in result.mappings().all()]

    async def get_race(self, race_id: int, viewer_id: int) -> dict:
        result = await self.db.execute(text(GET_RACE), {"p_race_id": race_id, "p_viewer_id": viewer_id})
        row = result.mappings().first()
        if row is None:
            raise HTTPException(status_code=404, detail="race_not_found")
        return _race_row(row)

    async def get_attendees(self, race_id: int, viewer_id: int) -> list[dict]:
        result = await self.db.execute(
            text(GET_ATTENDEES), {"p_race_id": race_id, "p_viewer_id": viewer_id}
        )
        return [_race_row(r) for r in result.mappings().all()]

    @staticmethod
    def _fields(body) -> dict:
        return {
            "p_name": body.name,
            "p_race_date": body.race_date,
            "p_start_time": body.start_time,
            "p_place": body.place,
            "p_zone": body.zone,
            "p_sport": body.sport,
            "p_distances": body.distances,
            "p_official_url": str(body.official_url) if body.official_url else None,
            "p_price": body.price,
        }

    async def create_race(self, user_id: int, body) -> int:
        result = await self.db.execute(text(CREATE_RACE), {"p_user_id": user_id, **self._fields(body)})
        race_id = result.mappings().first()["id"]
        await self.db.commit()
        return int(race_id)

    async def update_race(self, race_id: int, user_id: int, body) -> None:
        result = await self.db.execute(
            text(UPDATE_RACE), {"p_race_id": race_id, "p_user_id": user_id, **self._fields(body)}
        )
        status = result.mappings().first()["status"]
        if status != "ok":
            await self.db.rollback()
            _raise_status(status)
        await self.db.commit()

    async def delete_race(self, race_id: int, user_id: int) -> None:
        result = await self.db.execute(text(DELETE_RACE), {"p_race_id": race_id, "p_user_id": user_id})
        status = result.mappings().first()["status"]
        if status != "ok":
            await self.db.rollback()
            _raise_status(status)
        await self.db.commit()

    async def set_attendance(
        self, race_id: int, athlete_id: int, user_id: int, status: str, distance: str | None, registered: bool
    ) -> None:
        result = await self.db.execute(
            text(SET_ATTENDANCE),
            {
                "p_race_id": race_id,
                "p_athlete_id": athlete_id,
                "p_user_id": user_id,
                "p_status": status,
                "p_distance": distance,
                "p_registered": int(registered),
            },
        )
        res = result.mappings().first()["status"]
        if res != "ok":
            await self.db.rollback()
            _raise_status(res)
        await self.db.commit()

    async def find_similar(self, words: list[str], race_date: date | None, viewer_id: int) -> list[dict]:
        w = (words + [None, None, None])[:3]
        result = await self.db.execute(
            text(FIND_SIMILAR),
            {"p_w1": w[0], "p_w2": w[1], "p_w3": w[2], "p_date": race_date, "p_viewer_id": viewer_id},
        )
        return [dict(r) for r in result.mappings().all()]

    async def list_for_athlete(self, athlete_id: int, viewer_id: int, viewer_athlete_id: int | None) -> list[dict]:
        result = await self.db.execute(
            text(LIST_FOR_ATHLETE),
            {"p_athlete_id": athlete_id, "p_viewer_id": viewer_id, "p_viewer_athlete_id": viewer_athlete_id},
        )
        return [_race_row(r) for r in result.mappings().all()]

    async def public_list(self, limit: int) -> list[dict]:
        result = await self.db.execute(text(PUBLIC_LIST), {"p_limit": limit})
        return [_race_row(r) for r in result.mappings().all()]