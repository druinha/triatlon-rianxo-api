import json
from datetime import date

from fastapi import HTTPException
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.domains.members.plans.queries import (
    CREATE_GROUP,
    DELETE_GROUP,
    DELETE_PLAN,
    FOR_ATHLETE,
    GET_FOR_EDITOR,
    GROUP_MEMBERS,
    LIST_GROUPS,
    LIST_WEEK,
    PLAN_SESSIONS,
    PROGRESS,
    RENAME_GROUP,
    SAVE_PLAN,
    SESSIONS_FOR_ATHLETE,
    SET_DONE,
    SET_MEMBER,
)

_BOOL = ("is_minor", "in_group", "from_race", "can_mark", "done")
_JSON = ("races", "done")


def _row(row) -> dict:
    data = dict(row)
    for key in _JSON:
        if key in data and (data[key] is None or isinstance(data[key], str)):
            data[key] = json.loads(data[key]) if data[key] else []
    for key in _BOOL:
        if key in data and not isinstance(data[key], list):
            data[key] = bool(data[key])
    return data


def _raise_status(status: str, what: str = "plan") -> None:
    if status == "not_found":
        raise HTTPException(status_code=404, detail=f"{what}_not_found")
    if status == "forbidden":
        raise HTTPException(status_code=403, detail=f"{what}_forbidden")
    if status != "ok":
        raise HTTPException(status_code=500, detail="generic")


class PlanRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def _rows(self, query: str, params: dict) -> list[dict]:
        result = await self.db.execute(text(query), params)
        return [_row(r) for r in result.mappings().all()]

    async def _write(self, query: str, params: dict, what: str = "plan") -> dict:
        result = await self.db.execute(text(query), params)
        row = dict(result.mappings().first())
        if row["status"] != "ok":
            await self.db.rollback()
            _raise_status(row["status"], what)
        await self.db.commit()
        return row

    # ── Grupos ──
    async def list_groups(self, viewer_id: int) -> list[dict]:
        return await self._rows(LIST_GROUPS, {"p_viewer_id": viewer_id})

    async def create_group(self, viewer_id: int, name: str | None, race_id: int | None) -> int:
        row = await self._write(CREATE_GROUP, {"p_viewer_id": viewer_id, "p_name": name, "p_race_id": race_id}, "group")
        return row["id"]

    async def rename_group(self, group_id: int, viewer_id: int, name: str) -> None:
        await self._write(RENAME_GROUP, {"p_group_id": group_id, "p_viewer_id": viewer_id, "p_name": name}, "group")

    async def delete_group(self, group_id: int, viewer_id: int) -> None:
        await self._write(DELETE_GROUP, {"p_group_id": group_id, "p_viewer_id": viewer_id}, "group")

    async def group_members(self, group_id: int, viewer_id: int) -> list[dict]:
        return await self._rows(GROUP_MEMBERS, {"p_group_id": group_id, "p_viewer_id": viewer_id})

    async def set_member(self, group_id: int, viewer_id: int, athlete_id: int, mode: str) -> None:
        await self._write(
            SET_MEMBER,
            {"p_group_id": group_id, "p_viewer_id": viewer_id, "p_athlete_id": athlete_id, "p_mode": mode},
            "group",
        )

    # ── Plans (adestrador) ──
    async def list_week(self, viewer_id: int, week: date) -> list[dict]:
        return await self._rows(LIST_WEEK, {"p_viewer_id": viewer_id, "p_week": week})

    async def get_for_editor(
        self, viewer_id: int, week: date, scope: str, group_id: int | None, athlete_id: int | None
    ) -> dict | None:
        rows = await self._rows(
            GET_FOR_EDITOR,
            {"p_viewer_id": viewer_id, "p_week": week, "p_scope": scope, "p_group_id": group_id,
             "p_athlete_id": athlete_id},
        )
        return rows[0] if rows else None

    async def plan_sessions(self, plan_id: int) -> list[dict]:
        return await self._rows(PLAN_SESSIONS, {"p_plan_id": plan_id})

    async def save_plan(
        self, viewer_id: int, week: date, scope: str, group_id: int | None, athlete_id: int | None,
        status: str, note: str | None, sessions: list[dict],
    ) -> int:
        row = await self._write(
            SAVE_PLAN,
            {"p_viewer_id": viewer_id, "p_week": week, "p_scope": scope, "p_group_id": group_id,
             "p_athlete_id": athlete_id, "p_status": status, "p_note": note, "p_sessions": json.dumps(sessions)},
        )
        return row["id"]

    async def delete_plan(self, plan_id: int, viewer_id: int) -> None:
        await self._write(DELETE_PLAN, {"p_plan_id": plan_id, "p_viewer_id": viewer_id})

    async def progress(self, plan_id: int, viewer_id: int) -> list[dict]:
        return await self._rows(PROGRESS, {"p_plan_id": plan_id, "p_viewer_id": viewer_id})

    # ── Atleta ──
    async def for_athlete(self, athlete_id: int, viewer_id: int, week: date) -> dict:
        rows = await self._rows(FOR_ATHLETE, {"p_athlete_id": athlete_id, "p_viewer_id": viewer_id, "p_week": week})
        if not rows:
            raise HTTPException(status_code=404, detail="athlete_not_found")
        return rows[0]

    async def sessions_for_athlete(self, plan_id: int, athlete_id: int) -> list[dict]:
        return await self._rows(SESSIONS_FOR_ATHLETE, {"p_plan_id": plan_id, "p_athlete_id": athlete_id})

    async def set_done(
        self, session_id: int, athlete_id: int, viewer_id: int, done: bool, rpe: int | None, comment: str | None
    ) -> None:
        await self._write(
            SET_DONE,
            {"p_session_id": session_id, "p_athlete_id": athlete_id, "p_viewer_id": viewer_id,
             "p_done": int(done), "p_rpe": rpe, "p_comment": comment},
            "session",
        )
