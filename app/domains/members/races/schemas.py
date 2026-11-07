import re
from datetime import date, timedelta
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator

Zone = Literal["galicia", "spain", "portugal"]
RaceSport = Literal[
    "triathlon", "duathlon", "aquathlon", "running", "trail", "road_cycling", "mtb", "swimming", "open_water", "other"
]
Status = Literal["going", "maybe"]


class RaceIn(BaseModel):
    name: str = Field(min_length=3, max_length=160)
    race_date: date
    start_time: str | None = Field(default=None, pattern=r"^([01]\d|2[0-3]):[0-5]\d$")
    place: str = Field(min_length=2, max_length=120)
    zone: Zone = "galicia"
    sport: RaceSport
    distances: str | None = Field(default=None, max_length=200)
    official_url: HttpUrl | None = None
    # Texto libre: "25 €", "25 €, federados 20 €". Un número só pasa a "25 €".
    price: str | None = Field(default=None, max_length=80)
    # Ao crear: apuntar automaticamente o perfil propio de quen a engade
    join: bool = True

    @field_validator("name", "place")
    @classmethod
    def squash(cls, v: str) -> str:
        return " ".join(v.split())

    @field_validator("race_date")
    @classmethod
    def sane_date(cls, v: date) -> date:
        today = date.today()
        # Permite corrixir unha carreira de hai pouco; nada de séculos pasados nin futuros
        if not (today - timedelta(days=60) <= v <= today + timedelta(days=3 * 365)):
            raise ValueError("race_date_invalid")
        return v

    @field_validator("distances")
    @classmethod
    def clean_distances(cls, v: str | None) -> str | None:
        if v is None:
            return None
        parts = [" ".join(p.split()) for p in v.split(",")]
        return ", ".join(p for p in parts if p) or None

    @field_validator("price")
    @classmethod
    def clean_price(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = " ".join(v.split())
        if re.fullmatch(r"\d{1,4}([.,]\d{1,2})?", v):
            v = f"{v.replace('.', ',')} €"
        return v or None


class AttendanceIn(BaseModel):
    athlete_id: int
    status: Literal["going", "maybe", "none"]
    distance: str | None = Field(default=None, max_length=60)
    registered: bool = False


class Person(BaseModel):
    id: int
    full_name: str
    photo_file: str | None


class MyStatus(BaseModel):
    athlete_id: int
    status: Status


class RaceSummary(BaseModel):
    id: int
    name: str
    race_date: date
    start_time: str | None
    place: str
    zone: Zone
    sport: RaceSport
    distances: str | None
    official_url: str | None
    going_count: int
    maybe_count: int
    who: list[Person]
    mine: list[MyStatus]
    can_edit: bool


class Attendee(BaseModel):
    athlete_id: int
    full_name: str
    photo_file: str | None
    is_minor: bool
    status: Status
    distance: str | None
    registered: bool
    is_mine: bool


class RaceDetail(BaseModel):
    id: int
    name: str
    race_date: date
    start_time: str | None
    place: str
    zone: Zone
    sport: RaceSport
    distances: str | None
    official_url: str | None
    price: str | None
    is_past: bool
    going_count: int
    maybe_count: int
    can_edit: bool
    created_by_name: str | None
    attendees: list[Attendee]


class SimilarRace(BaseModel):
    id: int
    name: str
    race_date: date
    place: str
    going_count: int


class AthleteRace(BaseModel):
    id: int
    name: str
    race_date: date
    place: str
    sport: RaceSport
    status: Status
    distance: str | None
    registered: bool
    is_past: bool
    viewer_status: Status | None


class PublicRace(BaseModel):
    """Web pública: só carreiras onde vai alguén do clube, sen nomes nin cantos van.
    (O procedemento calcula going_count para filtrar, pero non se envía.)"""
    id: int
    name: str
    race_date: date
    start_time: str | None
    place: str
    zone: Zone
    sport: RaceSport
    distances: str | None
    official_url: str | None
    price: str | None
