from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class TravelPlanItem(BaseModel):
    time_label: str = Field(min_length=1, max_length=24)
    activity: str = Field(min_length=2, max_length=120)
    reason: str = Field(min_length=2, max_length=160)
    note: str = Field(default="待确认", max_length=200)


class TravelPlanDay(BaseModel):
    date: date
    title: str = Field(min_length=2, max_length=80)
    items: list[TravelPlanItem] = Field(min_length=1, max_length=5)


class TravelPlanPayload(BaseModel):
    summary: str = Field(min_length=10, max_length=300)
    days: list[TravelPlanDay] = Field(min_length=1, max_length=14)
    warnings: list[str] = Field(default_factory=list, max_length=8)

    @model_validator(mode="after")
    def reject_duplicate_dates(self) -> "TravelPlanPayload":
        dates = [day.date for day in self.days]
        if len(dates) != len(set(dates)):
            raise ValueError("travel plan dates must be unique")
        return self


class TravelPlanResponse(BaseModel):
    plan_id: str
    recommendation_session_id: str
    status: Literal["draft"]
    city: str
    check_in: date
    check_out: date
    guests: int
    provider: str
    model: str
    summary: str
    days: list[TravelPlanDay]
    warnings: list[str]
    created_at: datetime
