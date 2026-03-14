import json
import re
from datetime import date, datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from backend.schemas.estimate import EstimateItem


MONTH_ABBREVIATIONS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)


class FoodLogEntryOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str
    name: str
    description: str
    calories: str
    date: str
    time: str
    breakdown: list[EstimateItem]
    image: str | None = None
    protein: str | None = None
    carbs: str | None = None
    fat: str | None = None
    session_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("session_id", "sessionId"),
        serialization_alias="sessionId",
    )


class FoodLogListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    session_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("session_id", "sessionId"),
        serialization_alias="sessionId",
    )
    limit: int | None = None
    date_from: date | None = Field(
        default=None,
        validation_alias=AliasChoices("date_from", "dateFrom"),
        serialization_alias="dateFrom",
    )
    date_to: date | None = Field(
        default=None,
        validation_alias=AliasChoices("date_to", "dateTo"),
        serialization_alias="dateTo",
    )
    meal: str | None = None

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("session_id must be greater than 0")
        return value

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("limit must be greater than 0")
        return value

    @field_validator("meal")
    @classmethod
    def validate_meal(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        return normalized or None

    @field_validator("date_to")
    @classmethod
    def validate_date_range(cls, value: date | None, info) -> date | None:
        date_from = info.data.get("date_from")
        if value is not None and date_from is not None and value < date_from:
            raise ValueError("date_to cannot be earlier than date_from")
        return value


def serialize_food_log_entry(entry: dict[str, object]) -> FoodLogEntryOut:
    timestamp = _resolve_timestamp(entry)

    return FoodLogEntryOut.model_validate(
        {
            "id": str(entry["id"]),
            "name": entry["result_title"],
            "description": entry["result_description"],
            "calories": _normalize_calories(entry["total_calories"]),
            "date": _format_entry_date(timestamp),
            "time": _format_entry_time(timestamp),
            "breakdown": parse_food_log_items(entry["ingredients_json"]),
            "session_id": (
                str(entry["session_id"])
                if entry.get("session_id") is not None
                else None
            ),
        }
    )


def parse_food_log_items(value: object) -> list[EstimateItem]:
    if not isinstance(value, str):
        raise ValueError("ingredients_json must be a JSON string")

    parsed = json.loads(value)
    if not isinstance(parsed, list):
        raise ValueError("ingredients_json must decode to a list")
    return [EstimateItem.model_validate(item) for item in parsed]


def _resolve_timestamp(entry: dict[str, object]) -> datetime:
    candidates = (
        entry.get("logged_at"),
        entry.get("created_at"),
        entry.get("updated_at"),
    )
    for value in candidates:
        if not isinstance(value, str) or not value.strip():
            continue

        try:
            return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            continue

    return datetime(1970, 1, 1, 0, 0, 0)


def _format_entry_date(timestamp: datetime) -> str:
    return f"{MONTH_ABBREVIATIONS[timestamp.month - 1]} {timestamp.day}"


def _format_entry_time(timestamp: datetime) -> str:
    period = "AM" if timestamp.hour < 12 else "PM"
    hour = timestamp.hour % 12 or 12
    return f"{hour:02d}:{timestamp.minute:02d} {period}"


def _normalize_calories(value: object) -> str:
    if not isinstance(value, str):
        return "0"

    match = re.search(r"\d+(?:\.\d+)?", value.replace(",", ""))
    if match is None:
        return "0"
    return match.group(0)
