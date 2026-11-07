from datetime import date, datetime, timedelta
from typing import Any, Literal

from pydantic import BaseModel, Field, field_validator, model_validator

from app.domains.members.athlete_tests.zones import ZONE_KEYS

TestSport = Literal["swim", "bike", "run"]
TestKind = Literal["swim_200", "run_3000", "bike_ftp20", "bike_hr20", "bike_climb"]
SPORT_OF: dict[str, str] = {"swim_200": "swim", "run_3000": "run", "bike_ftp20": "bike", "bike_hr20": "bike",
                            "bike_climb": "bike"}
HR = Field(default=None, ge=40, le=230)


# ── Datos de cada tipo de test (o que escribe o atleta) ──
class SwimData(BaseModel):
    total_s: int = Field(ge=90, le=900)          # 200 m entre 1:30 e 15:00
    hr: int | None = HR


class RunSplit(BaseModel):
    m: int
    total_s: int = Field(ge=60, le=3600)
    hr: int | None = HR


class RunData(BaseModel):
    hr_warmup: int | None = HR
    hr_start: int | None = HR
    splits: list[RunSplit] = Field(min_length=6, max_length=6)

    @model_validator(mode="after")
    def check_splits(self):
        if [s.m for s in self.splits] != [500, 1000, 1500, 2000, 2500, 3000]:
            raise ValueError("splits_invalid")
        totals = [s.total_s for s in self.splits]
        if any(b <= a for a, b in zip(totals, totals[1:])):
            raise ValueError("splits_invalid")
        return self


class BikeFtpData(BaseModel):
    avg_watts: int = Field(ge=50, le=600)
    avg_hr: int | None = HR


class BikeHrData(BaseModel):
    avg_hr: int = Field(ge=80, le=230)


class BikeClimbData(BaseModel):
    climb: str = Field(min_length=2, max_length=80)
    total_s: int = Field(ge=60, le=4 * 3600)
    avg_hr: int | None = HR


DATA_MODELS = {"swim_200": SwimData, "run_3000": RunData, "bike_ftp20": BikeFtpData, "bike_hr20": BikeHrData,
               "bike_climb": BikeClimbData}

ZoneValue = int | list[int | None] | None


def check_zone_values(kind: str, values: dict[str, Any]) -> dict[str, ZoneValue]:
    keys = ZONE_KEYS.get(kind)
    if keys is None or set(values) != set(keys):
        raise ValueError("zones_invalid")
    out: dict[str, ZoneValue] = {}
    for k in keys:
        v = values[k]
        if v is None or (isinstance(v, int) and not isinstance(v, bool) and 0 < v < 10000):
            out[k] = v
        elif isinstance(v, list) and len(v) == 2 and all(x is None or (isinstance(x, int) and 0 <= x < 10000) for x in v):
            out[k] = v
        else:
            raise ValueError("zones_invalid")
    return out


class TestIn(BaseModel):
    kind: TestKind
    test_date: date
    data: dict[str, Any]

    @field_validator("test_date")
    @classmethod
    def sane_date(cls, v: date) -> date:
        today = date.today()
        if not (today - timedelta(days=2 * 365) <= v <= today):
            raise ValueError("test_date_invalid")
        return v

    @model_validator(mode="after")
    def check_data(self):
        self.data = DATA_MODELS[self.kind].model_validate(self.data).model_dump()
        return self

    @property
    def sport(self) -> str:
        return SPORT_OF[self.kind]


class ReviewIn(BaseModel):
    comment: str | None = Field(default=None, max_length=1000)
    # None = manter as zonas que xa tiña
    zones: dict[str, Any] | None = None


class ZonesIn(BaseModel):
    kind: Literal["swim_200", "run_3000", "bike_ftp20", "bike_hr20"]
    values: dict[str, Any]

    @model_validator(mode="after")
    def check(self):
        self.values = check_zone_values(self.kind, self.values)
        return self


class RemindIn(BaseModel):
    athlete_id: int
    sport: TestSport


# ── Respostas ──
class TestRow(BaseModel):
    id: int
    athlete_id: int
    sport: TestSport
    kind: TestKind
    test_date: date
    data: dict[str, Any]
    result_seconds: int | None
    result_value: int | None
    avg_hr: int | None
    status: Literal["submitted", "reviewed"]
    coach_comment: str | None
    created_at: datetime
    reviewed_at: datetime | None


class Zones(BaseModel):
    sport: TestSport
    confirmed_kind: str | None
    confirmed: dict[str, Any] | None
    confirmed_at: datetime | None
    provisional_kind: str | None
    provisional: dict[str, Any] | None
    provisional_test_id: int | None


class AthleteBrief(BaseModel):
    id: int
    full_name: str
    is_minor: bool
    photo_file: str | None


class AthleteTests(BaseModel):
    athlete: AthleteBrief
    can_review: bool
    due_days: int
    tests: list[TestRow]
    zones: list[Zones]


class PrevTest(BaseModel):
    id: int
    test_date: date
    data: dict[str, Any]
    result_seconds: int | None
    result_value: int | None
    avg_hr: int | None


class TestDetail(TestRow):
    athlete_name: str
    is_minor: bool
    photo_file: str | None
    reviewed_by_name: str | None
    can_review: bool
    can_delete: bool
    prev: PrevTest | None
    zones: Zones | None


class InboxItem(BaseModel):
    id: int
    athlete_id: int
    athlete_name: str
    is_minor: bool
    photo_file: str | None
    sport: TestSport
    kind: TestKind
    test_date: date
    result_seconds: int | None
    result_value: int | None
    avg_hr: int | None
    status: Literal["submitted", "reviewed"]
    created_at: datetime


class DueItem(BaseModel):
    athlete_id: int
    athlete_name: str
    is_minor: bool
    photo_file: str | None
    sport: TestSport
    last_date: date | None
    reminded_at: datetime | None
