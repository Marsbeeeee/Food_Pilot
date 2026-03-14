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
    saved_at: str = Field(
        validation_alias=AliasChoices("saved_at", "savedAt"),
        serialization_alias="savedAt",
    )
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


class FoodLogSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    source_type: str = Field(
        validation_alias=AliasChoices("source_type", "sourceType"),
        serialization_alias="sourceType",
    )
    meal_description: str = Field(
        validation_alias=AliasChoices("meal_description", "mealDescription"),
        serialization_alias="mealDescription",
    )
    result_title: str = Field(
        validation_alias=AliasChoices("result_title", "resultTitle"),
        serialization_alias="resultTitle",
    )
    result_confidence: str | None = Field(
        default=None,
        validation_alias=AliasChoices("result_confidence", "resultConfidence"),
        serialization_alias="resultConfidence",
    )
    result_description: str = Field(
        validation_alias=AliasChoices("result_description", "resultDescription"),
        serialization_alias="resultDescription",
    )
    total_calories: str = Field(
        validation_alias=AliasChoices("total_calories", "totalCalories", "total"),
        serialization_alias="totalCalories",
    )
    ingredients: list[EstimateItem]
    session_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("session_id", "sessionId"),
        serialization_alias="sessionId",
    )
    source_message_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("source_message_id", "sourceMessageId"),
        serialization_alias="sourceMessageId",
    )
    assistant_suggestion: str | None = Field(
        default=None,
        validation_alias=AliasChoices("assistant_suggestion", "assistantSuggestion"),
        serialization_alias="assistantSuggestion",
    )

    @field_validator(
        "source_type",
        "meal_description",
        "result_title",
        "result_description",
        "total_calories",
        "assistant_suggestion",
    )
    @classmethod
    def validate_text_fields(cls, value: str | None, info) -> str | None:
        if value is None:
            return None

        normalized = " ".join(value.strip().split())
        if normalized:
            return normalized
        raise ValueError(f"{info.field_name} cannot be empty")

    @field_validator("session_id", "source_message_id")
    @classmethod
    def validate_positive_ids(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("identifier must be greater than 0")
        return value


def serialize_food_log_entry(entry: dict[str, object]) -> FoodLogEntryOut:
    saved_at = _resolve_saved_at_value(entry)
    timestamp = _parse_saved_timestamp(saved_at)

    return FoodLogEntryOut.model_validate(
        {
            "id": str(entry["id"]),
            "name": entry["result_title"],
            "description": entry["result_description"],
            "calories": _normalize_calories(entry["total_calories"]),
            "date": _format_entry_date(timestamp),
            "time": _format_entry_time(timestamp),
            "breakdown": parse_food_log_items(entry["ingredients_json"]),
            "saved_at": saved_at,
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


def _resolve_saved_at_value(entry: dict[str, object]) -> str:
    candidates = (
        entry.get("updated_at"),
        entry.get("created_at"),
        entry.get("logged_at"),
    )
    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value
    return "1970-01-01 00:00:00"


def _parse_saved_timestamp(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
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
