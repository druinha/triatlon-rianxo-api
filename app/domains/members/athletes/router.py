from dataclasses import dataclass

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from fastapi.responses import FileResponse

from app.core.auth import AuthContext, get_auth_context
from app.core.config import get_settings
from app.domains.members.athletes.management import AthleteManagement
from app.domains.members.athletes.repository import AthleteRepository
from app.domains.members.athletes.schemas import DirectoryItem, ProfileResponse, ProfileUpdate

router = APIRouter(prefix="/athletes", tags=["athletes"])


@dataclass
class Context:
    user_id: int
    mgmt: AthleteManagement


async def get_athlete_ctx(ctx: AuthContext = Depends(get_auth_context)) -> Context:
    return Context(user_id=ctx.user_id, mgmt=AthleteManagement(AthleteRepository(ctx.db)))


async def read_limited(upload: UploadFile) -> bytes:
    limit = get_settings().photo_max_mb * 1024 * 1024
    data = await upload.read(limit + 1)
    if len(data) > limit:
        raise HTTPException(status_code=413, detail="image_too_large")
    if not data:
        raise HTTPException(status_code=422, detail="image_invalid")
    return data


@router.get("/", response_model=list[DirectoryItem])
async def list_athletes(ctx: Context = Depends(get_athlete_ctx)):
    return await ctx.mgmt.list_directory(ctx.user_id)


@router.get("/{athlete_id}", response_model=ProfileResponse)
async def get_profile(athlete_id: int, ctx: Context = Depends(get_athlete_ctx)):
    return await ctx.mgmt.get_profile(athlete_id, ctx.user_id)


# POST e non PUT: a API só acepta GET e POST (CORS e Caddy configurados así)
@router.post("/{athlete_id}", response_model=ProfileResponse)
async def update_profile(athlete_id: int, body: ProfileUpdate, ctx: Context = Depends(get_athlete_ctx)):
    return await ctx.mgmt.update_profile(athlete_id, ctx.user_id, body)


@router.post("/{athlete_id}/photo", response_model=ProfileResponse)
async def upload_photo(athlete_id: int, photo: UploadFile = File(...), ctx: Context = Depends(get_athlete_ctx)):
    data = await read_limited(photo)
    return await ctx.mgmt.set_photo(athlete_id, ctx.user_id, data)


@router.post("/{athlete_id}/photo/delete", response_model=ProfileResponse)
async def delete_photo(athlete_id: int, ctx: Context = Depends(get_athlete_ctx)):
    return await ctx.mgmt.remove_photo(athlete_id, ctx.user_id)


@router.get("/{athlete_id}/photo")
async def get_photo(athlete_id: int, ctx: Context = Depends(get_athlete_ctx)):
    path = await ctx.mgmt.get_photo_path(athlete_id, ctx.user_id)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="photo_not_found")
    # A web pide ?v=<ficheiro>: cada foto nova ten URL nova, así que pode quedar en caché
    return FileResponse(
        path,
        media_type="image/webp",
        headers={"Cache-Control": "private, max-age=31536000, immutable", "X-Content-Type-Options": "nosniff"},
    )
