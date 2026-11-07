import re
from datetime import date

from app.domains.members.races.repository import RaceRepository
from app.domains.members.races.schemas import AttendanceIn, RaceIn


# Palabras que non axudan a distinguir unha carreira doutra
STOPWORDS = {"de", "do", "da", "dos", "das", "del", "la", "las", "los", "el", "e", "y", "en", "a", "o", "the"}


def search_words(q: str) -> list[str]:
    """Ata 3 palabras significativas, as máis longas primeiro, xa escapadas para LIKE."""
    words = [w for w in re.split(r"[\s,.;:/()\-]+", q.lower()) if len(w) >= 3 and w not in STOPWORDS]
    words = sorted(dict.fromkeys(words), key=len, reverse=True)[:3]
    return [w.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") for w in words]


class RaceManagement:
    def __init__(self, repository: RaceRepository):
        self.database = repository

    async def list_races(self, viewer_id: int, only_mine: bool) -> list[dict]:
        return await self.database.list_races(viewer_id, only_mine)

    async def get_race(self, race_id: int, viewer_id: int) -> dict:
        race = await self.database.get_race(race_id, viewer_id)
        race["attendees"] = await self.database.get_attendees(race_id, viewer_id)
        return race

    async def create_race(self, user_id: int, own_athlete_id: int | None, body: RaceIn) -> dict:
        race_id = await self.database.create_race(user_id, body)
        # Quen a engade queda apuntado (se ten perfil de atleta propio)
        if body.join and own_athlete_id:
            await self.database.set_attendance(race_id, own_athlete_id, user_id, "going", None, False)
        return await self.get_race(race_id, user_id)

    async def update_race(self, race_id: int, user_id: int, body: RaceIn) -> dict:
        await self.database.update_race(race_id, user_id, body)
        return await self.get_race(race_id, user_id)

    async def delete_race(self, race_id: int, user_id: int) -> None:
        await self.database.delete_race(race_id, user_id)

    async def set_attendance(self, race_id: int, user_id: int, body: AttendanceIn) -> dict:
        await self.database.set_attendance(
            race_id, body.athlete_id, user_id, body.status, body.distance, body.registered
        )
        return await self.get_race(race_id, user_id)

    async def find_similar(self, q: str, race_date: date | None, viewer_id: int) -> list[dict]:
        words = search_words(q)
        if not words and race_date is None:
            return []
        return await self.database.find_similar(words, race_date, viewer_id)

    async def list_for_athlete(self, athlete_id: int, viewer_id: int, viewer_athlete_id: int | None) -> list[dict]:
        return await self.database.list_for_athlete(athlete_id, viewer_id, viewer_athlete_id)

    async def public_list(self, limit: int) -> list[dict]:
        return await self.database.public_list(limit)
