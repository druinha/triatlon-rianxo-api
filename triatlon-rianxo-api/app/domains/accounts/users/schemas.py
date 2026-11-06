from datetime import datetime
from typing import Literal

from pydantic import BaseModel


class UserListItem(BaseModel):
    id: int
    email: str
    display_name: str
    lang: Literal["gl", "es"]
    is_active: bool
    created_at: datetime
    last_login_at: datetime | None
    roles: list[str]
    minors: list[str]


class SetActiveRequest(BaseModel):
    active: bool


class ResetLinkRequest(BaseModel):
    lang: Literal["gl", "es"] = "gl"


class ResetLinkResponse(BaseModel):
    email: str
    display_name: str
    expires_at: datetime
    link: str
