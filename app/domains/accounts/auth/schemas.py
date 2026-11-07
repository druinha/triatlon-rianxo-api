from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class AthleteRef(BaseModel):
    id: int
    full_name: str
    is_minor: bool
    photo_file: str | None = None


class MeResponse(BaseModel):
    user_id: int
    email: str
    display_name: str
    lang: Literal["gl", "es"]
    roles: list[str]
    athletes: list[AthleteRef]


class TokenRequest(BaseModel):
    token: str = Field(min_length=20, max_length=200)


class ResetInfoResponse(BaseModel):
    email: str
    display_name: str
    expires_at: datetime


class ResetCompleteRequest(TokenRequest):
    password: str = Field(min_length=1, max_length=128)
