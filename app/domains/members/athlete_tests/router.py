from dataclasses import dataclass
from typing import Literal

from fastapi import APIRouter, Depends

from app.core.auth import AuthContext, get_auth_context, require_coach
from app.domains.members.athlete_tests.management import TestManagement
from app.domains.members.athlete_tests.repository import TestRepository
from app.domains.members.athlete_tests.schemas import (
    AthleteTests,
    DueItem,
    InboxItem,
    RemindIn,
    ReviewIn,
    TestDetail,
    TestIn,
    Zones,
    ZonesIn,
)

router = APIRouter(prefix="/tests", tags=["tests"])


@dataclass
class Context:
    user_id: int
    mgmt: TestManagement


async def get_test_ctx(ctx: AuthContext = Depends(get_auth_context)) -> Context:
    return Context(user_id=ctx.user_id, mgmt=TestManagement(TestRepository(ctx.db)))


async def get_coach_ctx(ctx: AuthContext = Depends(require_coach)) -> Context:
    return Context(user_id=ctx.user_id, mgmt=TestManagement(TestRepository(ctx.db)))


# ── Adestrador (as rutas fixas van antes que /{test_id}) ──
@router.get("/inbox", response_model=list[InboxItem])
async def inbox(status: Literal["submitted", "reviewed"] = "submitted", ctx: Context = Depends(get_coach_ctx)):
    return await ctx.mgmt.inbox(ctx.user_id, status)


@router.get("/due", response_model=list[DueItem])
async def due(ctx: Context = Depends(get_coach_ctx)):
    return await ctx.mgmt.due(ctx.user_id)


@router.post("/remind", status_code=204)
async def remind(body: RemindIn, ctx: Context = Depends(get_coach_ctx)):
    await ctx.mgmt.remind(ctx.user_id, body.athlete_id, body.sport)


# ── Atleta (ou titor, ou adestrador) ──
@router.get("/athlete/{athlete_id}", response_model=AthleteTests)
async def athlete_tests(athlete_id: int, ctx: Context = Depends(get_test_ctx)):
    return await ctx.mgmt.for_athlete(athlete_id, ctx.user_id)


@router.post("/athlete/{athlete_id}", response_model=TestDetail, status_code=201)
async def create_test(athlete_id: int, body: TestIn, ctx: Context = Depends(get_test_ctx)):
    return await ctx.mgmt.create(athlete_id, ctx.user_id, body)


@router.post("/athlete/{athlete_id}/zones", response_model=list[Zones])
async def set_zones(athlete_id: int, body: ZonesIn, ctx: Context = Depends(get_coach_ctx)):
    return await ctx.mgmt.set_zones(athlete_id, ctx.user_id, body)


@router.get("/{test_id}", response_model=TestDetail)
async def get_test(test_id: int, ctx: Context = Depends(get_test_ctx)):
    return await ctx.mgmt.get(test_id, ctx.user_id)


@router.post("/{test_id}/review", response_model=TestDetail)
async def review_test(test_id: int, body: ReviewIn, ctx: Context = Depends(get_coach_ctx)):
    return await ctx.mgmt.review(test_id, ctx.user_id, body)


@router.post("/{test_id}/delete", status_code=204)
async def delete_test(test_id: int, ctx: Context = Depends(get_test_ctx)):
    await ctx.mgmt.delete(test_id, ctx.user_id)
