from pathlib import Path

from starlette.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.images import delete_photo, new_photo_name, photo_path, process_photo, write_photo
from app.domains.members.athletes.repository import AthleteRepository
from app.domains.members.athletes.schemas import ProfileUpdate


class AthleteManagement:
    def __init__(self, repository: AthleteRepository):
        self.database = repository
        self.settings = get_settings()

    async def list_directory(self, viewer_id: int) -> list[dict]:
        return await self.database.list_directory(viewer_id)

    async def get_profile(self, athlete_id: int, viewer_id: int) -> dict:
        return await self.database.get_profile(athlete_id, viewer_id)

    async def update_profile(self, athlete_id: int, editor_id: int, body: ProfileUpdate) -> dict:
        await self.database.update_profile(
            athlete_id, editor_id, body.first_name, body.last_name, body.nickname, body.birth_date,
            body.license_number, body.chip_code, body.sports,
        )
        return await self.database.get_profile(athlete_id, editor_id)

    async def set_photo(self, athlete_id: int, editor_id: int, data: bytes) -> dict:
        # Procesar a imaxe bloquea a CPU: faise fóra do bucle de eventos
        webp = await run_in_threadpool(process_photo, data)
        name = new_photo_name()
        media = self.settings.media_dir
        await run_in_threadpool(write_photo, media, name, webp)
        try:
            old = await self.database.set_photo(athlete_id, editor_id, name)
        except Exception:
            # Sen permiso ou erro na BD: non deixar ficheiros orfos
            delete_photo(media, name)
            raise
        delete_photo(media, old)
        return await self.database.get_profile(athlete_id, editor_id)

    async def remove_photo(self, athlete_id: int, editor_id: int) -> dict:
        old = await self.database.set_photo(athlete_id, editor_id, None)
        delete_photo(self.settings.media_dir, old)
        return await self.database.get_profile(athlete_id, editor_id)

    async def get_photo_path(self, athlete_id: int, viewer_id: int) -> Path:
        name = await self.database.get_photo(athlete_id, viewer_id)
        return photo_path(self.settings.media_dir, name)
