from datetime import date, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

Scope = Literal["general", "group", "athlete"]
SessionSport = Literal["swim", "bike", "run", "gym", "rest", "race", "other"]


def check_monday(v: date) -> date:
    if v.weekday() != 0:
        raise ValueError("week_invalid")
    return v


class SessionIn(BaseModel):
    id: int | None = None
    day: int = Field(ge=0, le=6)
    sport: SessionSport
    title: str | None = Field(default=None, max_length=120)
    duration_min: int | None = Field(default=None, ge=1, le=1440)
    content: str | None = Field(default=None, max_length=4000)

    @field_validator("title")
    @classmethod
    def squash(cls, v: str | None) -> str | None:
        return " ".join(v.split()) or None if v else None

    @field_validator("content")
    @classmethod
    def trim(cls, v: str | None) -> str | None:
        return v.strip() or None if v else None


class PlanIn(BaseModel):
    week_start: date
    scope: Scope
    group_id: int | None = None
    athlete_id: int | None = None
    status: Literal["draft", "published"] = "draft"
    note: str | None = Field(default=None, max_length=500)
    sessions: list[SessionIn] = Field(default_factory=list, max_length=80)

    @field_validator("week_start")
    @classmethod
    def monday(cls, v: date) -> date:
        return check_monday(v)

    @model_validator(mode="after")
    def check_target(self):
        if self.scope == "general":
            self.group_id = self.athlete_id = None
        elif self.scope == "group":
            if not self.group_id:
                raise ValueError("group_required")
            self.athlete_id = None
        else:
            if not self.athlete_id:
                raise ValueError("athlete_required")
            self.group_id = None
        return self


class GroupIn(BaseModel):
    name: str | None = Field(default=None, max_length=120)
    race_id: int | None = None

    @model_validator(mode="after")
    def need_something(self):
        self.name = " ".join(self.name.split()) if self.name else None
        if not self.name and not self.race_id:
            raise ValueError("name_required")
        return self


class GroupRename(BaseModel):
    name: str = Field(min_length=1, max_length=120)


class MemberIn(BaseModel):
    athlete_id: int
    mode: Literal["add", "exclude", "none"]


class DoneIn(BaseModel):
    athlete_id: int
    done: bool = True
    rpe: int | None = Field(default=None, ge=1, le=10)
    comment: str | None = Field(default=None, max_length=500)


# ── Respostas ──
class Group(BaseModel):
    id: int
    name: str
    race_id: int | None
    race_name: str | None
    race_date: date | None
    member_count: int


class GroupMember(BaseModel):
    athlete_id: int
    full_name: str
    is_minor: bool
    photo_file: str | None
    in_group: bool
    from_race: bool
    mode: Literal["add", "exclude"] | None


class Session(BaseModel):
    id: int
    day: int
    position: int
    sport: SessionSport
    title: str | None
    duration_min: int | None
    content: str | None


class PlanRow(BaseModel):
    id: int
    week_start: date
    scope: Scope
    group_id: int | None
    athlete_id: int | None
    status: Literal["draft", "published"]
    note: str | None
    published_at: datetime | None
    updated_at: datetime


class EditorPlan(BaseModel):
    plan: PlanRow | None
    sessions: list[Session]


class WeekPlan(BaseModel):
    id: int
    week_start: date
    scope: Scope
    group_id: int | None
    group_name: str | None
    athlete_id: int | None
    athlete_name: str | None
    status: Literal["draft", "published"]
    published_at: datetime | None
    updated_at: datetime
    session_count: int


class AthleteSession(Session):
    done: bool
    rpe: int | None
    comment: str | None
    done_at: datetime | None


class RaceBrief(BaseModel):
    id: int
    name: str
    race_date: date
    place: str


class AthleteWeek(BaseModel):
    athlete_id: int
    full_name: str
    is_minor: bool
    photo_file: str | None
    can_mark: bool
    week_start: date
    plan_id: int | None
    scope: Scope | None
    group_name: str | None
    note: str | None
    published_at: datetime | None
    races: list[RaceBrief]
    sessions: list[AthleteSession]


class ProgressRow(BaseModel):
    athlete_id: int
    full_name: str
    is_minor: bool
    photo_file: str | None
    done: list[dict[str, Any]]


class ImportedSession(BaseModel):
    sport: SessionSport
    title: str | None
    duration_min: int | None
    content: str | None


class ImportResult(BaseModel):
    title: str | None
    days: list[list[ImportedSession]]
