from datetime import datetime
from typing import Literal

from pydantic import BaseModel, EmailStr, Field, model_validator

Lang = Literal["gl", "es"]
Kind = Literal["member", "guardian"]


class InvitationCreate(BaseModel):
    email: EmailStr
    invited_name: str = Field(min_length=2, max_length=160)
    kind: Kind = "member"
    minor_name: str | None = Field(default=None, max_length=160)
    is_athlete: bool = True
    grant_admin: bool = False
    grant_coach: bool = False
    lang: Lang = "gl"  # idioma da páxina á que leva a ligazón

    @model_validator(mode="after")
    def check_kind(self):
        if self.kind == "guardian":
            if not self.minor_name or len(self.minor_name.strip()) < 2:
                raise ValueError("minor_name_required")
            # Un titor non recibe roles de staff nesta invitación
            self.is_athlete = False
            self.grant_admin = False
            self.grant_coach = False
        else:
            self.minor_name = None
        return self


class InvitationRenew(BaseModel):
    lang: Lang = "gl"


class InvitationLink(BaseModel):
    id: int
    email: str
    invited_name: str
    kind: Kind
    minor_name: str | None
    expires_at: datetime
    link: str


class InvitationListItem(BaseModel):
    id: int
    email: str
    invited_name: str
    kind: Kind
    minor_name: str | None
    is_athlete: bool
    grant_admin: bool
    grant_coach: bool
    created_at: datetime
    expires_at: datetime
    used_at: datetime | None
    revoked_at: datetime | None
    status: Literal["pending", "used", "revoked", "expired"]
    created_by_name: str | None
    used_by_name: str | None


class InvitationStatus(BaseModel):
    id: int
    status: str


class InvitationCheck(BaseModel):
    token: str = Field(min_length=20, max_length=200)


class InvitationInfo(BaseModel):
    email: str
    invited_name: str
    kind: Kind
    minor_name: str | None
    expires_at: datetime
    email_registered: bool


class InvitationAccept(InvitationCheck):
    password: str = Field(min_length=1, max_length=128)
    display_name: str | None = Field(default=None, max_length=120)
    lang: Lang = "gl"
    consent: bool = False
