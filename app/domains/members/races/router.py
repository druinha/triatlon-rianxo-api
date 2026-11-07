from dataclasses import dataclass
from datetime import date

from fastapi import APIRouter, Depends, Query, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import AuthContext, get_auth_context, get_public_db
from app.domains.members.races.management import RaceManagement
from app.domains.members.races.repository import RaceRepository
from app.domains.members.races.schemas import (
    AthleteRace,
    AttendanceIn,
    PublicRace,
    RaceDetail,
    RaceIn,
    RaceSummary,
    SimilarRace,
)

router = APIRouter(prefix="/races", tags=["races"])
public_router = APIRouter(prefix="/public", tags=["public"])


@dataclass
class Context:
    user_id: int
    own_athlete_id: int | None  # perfil adulto propio (non os fillos)
    mgmt: RaceManagement


async def get_race_ctx(ctx: AuthContext = Depends(get_auth_context)) -> Context:
    own = next((a["id"] for a in ctx.user.get("athletes", []) if not a.get("is_minor")), None)
    return Context(user_id=ctx.user_id, own_athlete_id=own, mgmt=RaceManagement(RaceRepository(ctx.db)))


# As rutas fixas van antes que /{race_id}
@router.get("/", response_model=list[RaceSummary])
async def list_races(mine: bool = False, ctx: Context = Depends(get_race_ctx)):
    return await ctx.mgmt.list_races(ctx.user_id, mine)


@router.get("/similar", response_model=list[SimilarRace])
async def similar_races(
    q: str = Query(default="", max_length=160),
    race_date: date | None = Query(default=None, alias="date"),
    ctx: Context = Depends(get_race_ctx),
):
    return await ctx.mgmt.find_similar(q, race_date, ctx.user_id)


@router.get("/athlete/{athlete_id}", response_model=list[AthleteRace])
async def races_for_athlete(athlete_id: int, ctx: Context = Depends(get_race_ctx)):
    return await ctx.mgmt.list_for_athlete(athlete_id, ctx.user_id, ctx.own_athlete_id)


@router.post("/", response_model=RaceDetail, status_code=201)
async def create_race(body: RaceIn, ctx: Context = Depends(get_race_ctx)):
    return await ctx.mgmt.create_race(ctx.user_id, ctx.own_athlete_id, body)


@router.get("/{race_id}", response_model=RaceDetail)
async def get_race(race_id: int, ctx: Context = Depends(get_race_ctx)):
    return await ctx.mgmt.get_race(race_id, ctx.user_id)


@router.post("/{race_id}", response_model=RaceDetail)
async def update_race(race_id: int, body: RaceIn, ctx: Context = Depends(get_race_ctx)):
    return await ctx.mgmt.update_race(race_id, ctx.user_id, body)


@router.post("/{race_id}/delete", status_code=204)
async def delete_race(race_id: int, ctx: Context = Depends(get_race_ctx)):
    await ctx.mgmt.delete_race(race_id, ctx.user_id)


@router.post("/{race_id}/attendance", response_model=RaceDetail)
async def set_attendance(race_id: int, body: AttendanceIn, ctx: Context = Depends(get_race_ctx)):
    return await ctx.mgmt.set_attendance(race_id, ctx.user_id, body)


# ── Web pública (sen sesión): só contadores, nunca nomes ──
@public_router.get("/races", response_model=list[PublicRace])
async def public_races(response: Response, limit: int = Query(default=60, ge=1, le=200),
                       db: AsyncSession = Depends(get_public_db)):
    response.headers["Cache-Control"] = "public, max-age=300"
    return await RaceManagement(RaceRepository(db)).public_list(limit)
