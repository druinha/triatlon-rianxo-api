from datetime import date, timedelta

from starlette.concurrency import run_in_threadpool

from app.domains.members.plans import export, importer
from app.domains.members.plans.repository import PlanRepository
from app.domains.members.plans.schemas import DoneIn, GroupIn, PlanIn


def monday_of(d: date) -> date:
    return d - timedelta(days=d.weekday())


class PlanManagement:
    def __init__(self, repository: PlanRepository):
        self.database = repository

    # ── Grupos ──
    async def list_groups(self, viewer_id: int) -> list[dict]:
        return await self.database.list_groups(viewer_id)

    async def create_group(self, viewer_id: int, body: GroupIn) -> dict:
        group_id = await self.database.create_group(viewer_id, body.name, body.race_id)
        return next(g for g in await self.database.list_groups(viewer_id) if g["id"] == group_id)

    async def rename_group(self, group_id: int, viewer_id: int, name: str) -> None:
        await self.database.rename_group(group_id, viewer_id, " ".join(name.split()))

    async def delete_group(self, group_id: int, viewer_id: int) -> None:
        await self.database.delete_group(group_id, viewer_id)

    async def group_members(self, group_id: int, viewer_id: int) -> list[dict]:
        return await self.database.group_members(group_id, viewer_id)

    async def set_member(self, group_id: int, viewer_id: int, athlete_id: int, mode: str) -> list[dict]:
        await self.database.set_member(group_id, viewer_id, athlete_id, mode)
        return await self.database.group_members(group_id, viewer_id)

    # ── Plans (adestrador) ──
    async def list_week(self, viewer_id: int, week: date) -> list[dict]:
        return await self.database.list_week(viewer_id, week)

    async def editor(
        self, viewer_id: int, week: date, scope: str, group_id: int | None, athlete_id: int | None
    ) -> dict:
        plan = await self.database.get_for_editor(viewer_id, week, scope, group_id, athlete_id)
        sessions = await self.database.plan_sessions(plan["id"]) if plan else []
        return {"plan": plan, "sessions": sessions}

    async def save(self, viewer_id: int, body: PlanIn) -> dict:
        # A orde dentro de cada día é a orde en que chegan
        pos = [0] * 7
        sessions = []
        for s in body.sessions:
            sessions.append({**s.model_dump(), "position": pos[s.day]})
            pos[s.day] += 1
        await self.database.save_plan(
            viewer_id, body.week_start, body.scope, body.group_id, body.athlete_id, body.status, body.note, sessions
        )
        return await self.editor(viewer_id, body.week_start, body.scope, body.group_id, body.athlete_id)

    async def delete(self, plan_id: int, viewer_id: int) -> None:
        await self.database.delete_plan(plan_id, viewer_id)

    async def progress(self, plan_id: int, viewer_id: int) -> list[dict]:
        return await self.database.progress(plan_id, viewer_id)

    async def export_progress(self, plan_id: int, viewer_id: int, lang: str) -> tuple[bytes, str]:
        plan = await self.database.get_plan(plan_id, viewer_id)
        sessions = await self.database.plan_sessions(plan_id)
        rows = await self.database.progress(plan_id, viewer_id)
        data = await run_in_threadpool(export.build, plan, sessions, rows, lang)
        name = f"{'seguimento' if lang == 'gl' else 'seguimiento'}-{plan['week_start']:%Y-%m-%d}.xlsx"
        return data, name

    async def import_file(self, filename: str, data: bytes) -> dict:
        # Ler Excel/Word bloquea a CPU: fóra do bucle de eventos
        return await run_in_threadpool(importer.parse_file, filename, data)

    # ── Atleta ──
    async def for_athlete(self, athlete_id: int, viewer_id: int, week: date) -> dict:
        week = monday_of(week)
        data = await self.database.for_athlete(athlete_id, viewer_id, week)
        data["week_start"] = week
        data["sessions"] = await self.database.sessions_for_athlete(data["plan_id"], athlete_id) if data["plan_id"] else []
        return data

    async def set_done(self, session_id: int, viewer_id: int, body: DoneIn) -> None:
        await self.database.set_done(session_id, body.athlete_id, viewer_id, body.done, body.rpe, body.comment)
