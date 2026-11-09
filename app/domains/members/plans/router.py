from dataclasses import dataclass
from datetime import date

from typing import Literal

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile

from app.core.auth import AuthContext, get_auth_context, require_coach
from app.domains.members.plans.management import PlanManagement, monday_of
from app.domains.members.plans.repository import PlanRepository
from app.domains.members.plans.schemas import (
    AthleteWeek,
    DoneIn,
    EditorPlan,
    Group,
    GroupIn,
    GroupMember,
    GroupRename,
    ImportResult,
    MemberIn,
    PlanIn,
    ProgressRow,
    Scope,
    WeekPlan,
)

router = APIRouter(prefix="/plans", tags=["plans"])
IMPORT_MAX_BYTES = 5 * 1024 * 1024


@dataclass
class Context:
    user_id: int
    mgmt: PlanManagement


async def get_plan_ctx(ctx: AuthContext = Depends(get_auth_context)) -> Context:
    return Context(user_id=ctx.user_id, mgmt=PlanManagement(PlanRepository(ctx.db)))


async def get_coach_ctx(ctx: AuthContext = Depends(require_coach)) -> Context:
    return Context(user_id=ctx.user_id, mgmt=PlanManagement(PlanRepository(ctx.db)))


def _monday(week: date) -> date:
    if week.weekday() != 0:
        raise HTTPException(status_code=422, detail="week_invalid")
    return week


# ── Grupos (adestrador) ──
@router.get("/groups", response_model=list[Group])
async def list_groups(ctx: Context = Depends(get_coach_ctx)):
    return await ctx.mgmt.list_groups(ctx.user_id)


@router.post("/groups", response_model=Group, status_code=201)
async def create_group(body: GroupIn, ctx: Context = Depends(get_coach_ctx)):
    return await ctx.mgmt.create_group(ctx.user_id, body)


@router.get("/groups/{group_id}/members", response_model=list[GroupMember])
async def group_members(group_id: int, ctx: Context = Depends(get_coach_ctx)):
    return await ctx.mgmt.group_members(group_id, ctx.user_id)


@router.post("/groups/{group_id}/members", response_model=list[GroupMember])
async def set_member(group_id: int, body: MemberIn, ctx: Context = Depends(get_coach_ctx)):
    return await ctx.mgmt.set_member(group_id, ctx.user_id, body.athlete_id, body.mode)


@router.post("/groups/{group_id}", status_code=204)
async def rename_group(group_id: int, body: GroupRename, ctx: Context = Depends(get_coach_ctx)):
    await ctx.mgmt.rename_group(group_id, ctx.user_id, body.name)


@router.post("/groups/{group_id}/delete", status_code=204)
async def delete_group(group_id: int, ctx: Context = Depends(get_coach_ctx)):
    await ctx.mgmt.delete_group(group_id, ctx.user_id)


# ── Plans (adestrador) ──
@router.get("/week", response_model=list[WeekPlan])
async def list_week(week: date, ctx: Context = Depends(get_coach_ctx)):
    return await ctx.mgmt.list_week(ctx.user_id, _monday(week))


@router.get("/editor", response_model=EditorPlan)
async def editor(
    week: date, scope: Scope = "general", group_id: int | None = None, athlete_id: int | None = None,
    ctx: Context = Depends(get_coach_ctx),
):
    if scope == "general":
        group_id = athlete_id = None
    elif scope == "group":
        athlete_id = None
    else:
        group_id = None
    return await ctx.mgmt.editor(ctx.user_id, _monday(week), scope, group_id, athlete_id)


@router.post("/", response_model=EditorPlan)
async def save_plan(body: PlanIn, ctx: Context = Depends(get_coach_ctx)):
    return await ctx.mgmt.save(ctx.user_id, body)


@router.post("/import", response_model=ImportResult)
async def import_plan(file: UploadFile = File(...), ctx: Context = Depends(get_coach_ctx)):
    data = await file.read(IMPORT_MAX_BYTES + 1)
    if len(data) > IMPORT_MAX_BYTES:
        raise HTTPException(status_code=413, detail="import_too_large")
    if not data:
        raise HTTPException(status_code=422, detail="import_unreadable")
    return await ctx.mgmt.import_file(file.filename or "", data)


@router.get("/{plan_id}/progress", response_model=list[ProgressRow])
async def progress(plan_id: int, ctx: Context = Depends(get_coach_ctx)):
    return await ctx.mgmt.progress(plan_id, ctx.user_id)


@router.get("/{plan_id}/progress.xlsx")
async def export_progress(plan_id: int, lang: Literal["gl", "es"] = "gl", ctx: Context = Depends(get_coach_ctx)):
    data, name = await ctx.mgmt.export_progress(plan_id, ctx.user_id, lang)
    return Response(
        content=data,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{name}"', "Cache-Control": "no-store"},
    )


@router.post("/{plan_id}/delete", status_code=204)
async def delete_plan(plan_id: int, ctx: Context = Depends(get_coach_ctx)):
    await ctx.mgmt.delete(plan_id, ctx.user_id)


# ── Atleta (ou titor, ou adestrador mirando) ──
@router.get("/athlete/{athlete_id}", response_model=AthleteWeek)
async def athlete_week(athlete_id: int, week: date | None = Query(default=None), ctx: Context = Depends(get_plan_ctx)):
    return await ctx.mgmt.for_athlete(athlete_id, ctx.user_id, week or monday_of(date.today()))


@router.post("/sessions/{session_id}/done", status_code=204)
async def set_done(session_id: int, body: DoneIn, ctx: Context = Depends(get_plan_ctx)):
    await ctx.mgmt.set_done(session_id, ctx.user_id, body)
