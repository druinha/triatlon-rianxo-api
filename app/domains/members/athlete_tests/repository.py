import json
from datetime import date

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.members.athlete_tests.queries import (
    CREATE_TEST,
    DELETE_TEST,
    GET_TEST,
    INBOX,
    LIST_DUE,
    LIST_FOR_ATHLETE,
    LIST_ZONES,
    REMIND,
    REVIEW_TEST,
    SET_ZONES,
    TEST_ACCESS,
)

_JSON = ("data", "prev_data", "confirmed", "provisional")
_BOOL = ("is_minor", "can_review", "can_delete")


def _row(row) -> dict:
    data = dict(row)
    for key in _JSON:
        if key in data and isinstance(data[key], str):
            data[key] = json.loads(data[key])
    for key in _BOOL:
        if key in data:
            data[key] = bool(data[key])
    return data


def _raise_status(status: str) -> None:
    if status == "not_found":
        raise HTTPException(status_code=404, detail="test_not_found")
    if status == "forbidden":
        raise HTTPException(status_code=403, detail="test_forbidden")
    if status != "ok":
        raise HTTPException(status_code=500, detail="generic")


def _dump(value) -> str | None:
    return None if value is None else json.dumps(value)


class TestRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def access(self, athlete_id: int, viewer_id: int) -> dict:
        result = await self.db.execute(text(TEST_ACCESS), {"p_athlete_id": athlete_id, "p_viewer_id": viewer_id})
        row = result.mappings().first()
        if row is None:
            raise HTTPException(status_code=404, detail="athlete_not_found")
        data = _row(row)
        if data["access"] not in ("manage", "staff"):
            raise HTTPException(status_code=403, detail="test_forbidden")
        return data

    async def list_for_athlete(self, athlete_id: int, viewer_id: int) -> list[dict]:
        result = await self.db.execute(
            text(LIST_FOR_ATHLETE), {"p_athlete_id": athlete_id, "p_viewer_id": viewer_id}
        )
        return [_row(r) for r in result.mappings().all()]

    async def list_zones(self, athlete_id: int, viewer_id: int) -> list[dict]:
        result = await self.db.execute(text(LIST_ZONES), {"p_athlete_id": athlete_id, "p_viewer_id": viewer_id})
        return [_row(r) for r in result.mappings().all()]

    async def create(
        self, athlete_id: int, editor_id: int, sport: str, kind: str, test_date: date, data: dict,
        result_seconds: int | None, result_value: int | None, avg_hr: int | None, zones: dict | None,
    ) -> int:
        result = await self.db.execute(
            text(CREATE_TEST),
            {
                "p_athlete_id": athlete_id, "p_editor_id": editor_id, "p_sport": sport, "p_kind": kind,
                "p_test_date": test_date, "p_data": json.dumps(data), "p_result_seconds": result_seconds,
                "p_result_value": result_value, "p_avg_hr": avg_hr, "p_zones": _dump(zones),
            },
        )
        row = result.mappings().first()
        if row["status"] != "ok":
            await self.db.rollback()
            _raise_status(row["status"])
        await self.db.commit()
        return row["id"]

    async def get(self, test_id: int, viewer_id: int) -> dict:
        result = await self.db.execute(text(GET_TEST), {"p_test_id": test_id, "p_viewer_id": viewer_id})
        row = result.mappings().first()
        if row is None:
            raise HTTPException(status_code=404, detail="test_not_found")
        return _row(row)

    async def inbox(self, viewer_id: int, status: str, limit: int) -> list[dict]:
        result = await self.db.execute(
            text(INBOX), {"p_viewer_id": viewer_id, "p_status": status, "p_limit": limit}
        )
        return [_row(r) for r in result.mappings().all()]

    async def _write(self, query: str, params: dict) -> None:
        result = await self.db.execute(text(query), params)
        status = result.mappings().first()["status"]
        if status != "ok":
            await self.db.rollback()
            _raise_status(status)
        await self.db.commit()

    async def review(self, test_id: int, viewer_id: int, comment: str | None, zones: dict | None) -> None:
        await self._write(
            REVIEW_TEST,
            {"p_test_id": test_id, "p_viewer_id": viewer_id, "p_comment": comment, "p_zones": _dump(zones)},
        )

    async def set_zones(self, athlete_id: int, viewer_id: int, sport: str, kind: str, zones: dict) -> None:
        await self._write(
            SET_ZONES,
            {"p_athlete_id": athlete_id, "p_viewer_id": viewer_id, "p_sport": sport, "p_kind": kind,
             "p_zones": json.dumps(zones)},
        )

    async def delete(self, test_id: int, viewer_id: int) -> None:
        await self._write(DELETE_TEST, {"p_test_id": test_id, "p_viewer_id": viewer_id})

    async def list_due(self, viewer_id: int, days: int) -> list[dict]:
        result = await self.db.execute(text(LIST_DUE), {"p_viewer_id": viewer_id, "p_days": days})
        return [_row(r) for r in result.mappings().all()]

    async def remind(self, viewer_id: int, athlete_id: int, sport: str) -> None:
        await self._write(REMIND, {"p_viewer_id": viewer_id, "p_athlete_id": athlete_id, "p_sport": sport})
