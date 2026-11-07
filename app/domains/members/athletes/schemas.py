from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, field_validator

# Claves de deportes (a web tradúceas). Teñen que coincidir co ENUM de athlete_sports.
Sport = Literal[
    "triathlon", "duathlon", "aquathlon", "running", "trail", "road_cycling", "mtb", "swimming", "open_water"
]
Access = Literal["manage", "staff", "basic"]


class DirectoryItem(BaseModel):
    id: int
    full_name: str
    is_minor: bool
    photo_file: str | None
    sports: list[Sport]
    access: Access


class ProfileResponse(BaseModel):
    id: int
    # O nome que ven todos: o alcume se o hai; se non, nome e apelidos
    full_name: str
    nickname: str | None
    is_minor: bool
    is_active: bool
    photo_file: str | None
    # Só para quen ten acceso completo (o propio atleta, titores, adestradores e admins)
    first_name: str | None
    last_name: str | None
    birth_date: date | None
    license_number: str | None
    chip_code: str | None
    guardians: list[str]
    sports: list[Sport]
    access: Access
    can_edit: bool
    updated_at: datetime


class ProfileUpdate(BaseModel):
    first_name: str = Field(min_length=1, max_length=80)
    last_name: str | None = Field(default=None, max_length=120)
    # Alcume ou nome polo que o coñecen: é o que ven os demais. Baleiro = nome e apelidos.
    nickname: str | None = Field(default=None, max_length=60)
    birth_date: date | None = None
    license_number: str | None = Field(default=None, max_length=40)
    chip_code: str | None = Field(default=None, max_length=40)
    sports: list[Sport] = Field(default_factory=list, max_length=9)

    @field_validator("first_name")
    @classmethod
    def strip_first(cls, v: str) -> str:
        v = " ".join(v.split())
        if not v:
            raise ValueError("name_required")
        return v

    @field_validator("last_name", "nickname")
    @classmethod
    def strip_optional(cls, v: str | None) -> str | None:
        if v is None:
            return None
        return " ".join(v.split()) or None

    @field_validator("birth_date")
    @classmethod
    def check_birth_date(cls, v: date | None) -> date | None:
        if v is not None and not (date(1920, 1, 1) <= v <= date.today()):
            raise ValueError("birth_date_invalid")
        return v

    @field_validator("license_number", "chip_code")
    @classmethod
    def clean_code(cls, v: str | None) -> str | None:
        if v is None:
            return None
        v = v.strip()
        if v and not all(c.isalnum() or c in "-/ " for c in v):
            raise ValueError("code_invalid")
        return v or None

    @field_validator("sports")
    @classmethod
    def unique_sports(cls, v: list[str]) -> list[str]:
        return sorted(set(v))
