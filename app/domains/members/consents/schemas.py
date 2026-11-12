from datetime import datetime

from pydantic import BaseModel


class ConsentIn(BaseModel):
    training: bool
    img_web: bool
    img_social: bool
    img_whatsapp: bool
    img_print: bool


class ConsentRow(BaseModel):
    athlete_id: int
    full_name: str
    is_minor: bool
    photo_file: str | None = None
    training: bool | None = None
    img_web: bool | None = None
    img_social: bool | None = None
    img_whatsapp: bool | None = None
    img_print: bool | None = None
    version: str | None = None
    updated_at: datetime | None = None
    pending: bool = False


class ConsentSaved(BaseModel):
    wiped: bool
    row: ConsentRow
