from fastapi import HTTPException

from app.domains.members.athlete_tests import zones as calc
from app.domains.members.athlete_tests.repository import TestRepository
from app.domains.members.athlete_tests.schemas import SPORT_OF, ReviewIn, TestIn, ZonesIn, check_zone_values

# Cada canto hai que repetir un test (o atleta ve o aviso e o adestrador a lista)
DUE_DAYS = 180

_PREV = ("id", "test_date", "data", "result_seconds", "result_value", "avg_hr")
_ZONES = ("confirmed_kind", "confirmed", "confirmed_at", "provisional_kind", "provisional", "provisional_test_id")


class TestManagement:
    def __init__(self, repository: TestRepository):
        self.database = repository

    async def for_athlete(self, athlete_id: int, viewer_id: int) -> dict:
        acc = await self.database.access(athlete_id, viewer_id)
        return {
            "athlete": {k: acc[k] for k in ("id", "full_name", "is_minor", "photo_file")},
            "can_review": acc["can_review"],
            "due_days": DUE_DAYS,
            "tests": await self.database.list_for_athlete(athlete_id, viewer_id),
            "zones": await self.database.list_zones(athlete_id, viewer_id),
        }

    async def create(self, athlete_id: int, editor_id: int, body: TestIn) -> dict:
        results, zones = calc.compute(body.kind, body.data)
        test_id = await self.database.create(
            athlete_id, editor_id, body.sport, body.kind, body.test_date, body.data,
            results["result_seconds"], results["result_value"], results["avg_hr"], zones,
        )
        return await self.get(test_id, editor_id)

    async def get(self, test_id: int, viewer_id: int) -> dict:
        row = await self.database.get(test_id, viewer_id)
        row["prev"] = {k: row["prev_date" if k == "test_date" else f"prev_{k}"] for k in _PREV} if row["prev_id"] else None
        has_zones = any(row[k] is not None for k in ("confirmed", "provisional"))
        row["zones"] = {"sport": row["sport"], **{k: row[k] for k in _ZONES}} if has_zones else None
        return row

    async def inbox(self, viewer_id: int, status: str) -> list[dict]:
        return await self.database.inbox(viewer_id, status, 100)

    async def review(self, test_id: int, viewer_id: int, body: ReviewIn) -> dict:
        zones = None
        if body.zones is not None:
            test = await self.database.get(test_id, viewer_id)
            if test["kind"] == "bike_climb":
                raise HTTPException(status_code=422, detail="zones_invalid")
            try:
                zones = check_zone_values(test["kind"], body.zones)
            except ValueError:
                raise HTTPException(status_code=422, detail="zones_invalid")
        await self.database.review(test_id, viewer_id, body.comment, zones)
        return await self.get(test_id, viewer_id)

    async def set_zones(self, athlete_id: int, viewer_id: int, body: ZonesIn) -> list[dict]:
        await self.database.set_zones(athlete_id, viewer_id, SPORT_OF[body.kind], body.kind, body.values)
        return await self.database.list_zones(athlete_id, viewer_id)

    async def delete(self, test_id: int, viewer_id: int) -> None:
        await self.database.delete(test_id, viewer_id)

    async def due(self, viewer_id: int) -> list[dict]:
        return await self.database.list_due(viewer_id, DUE_DAYS)

    async def remind(self, viewer_id: int, athlete_id: int, sport: str) -> None:
        await self.database.remind(viewer_id, athlete_id, sport)
