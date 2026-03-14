import json
import re
from datetime import date, datetime
from typing import Literal

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from backend.schemas.estimate import EstimateItem, EstimateResult


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
    meal_occurred_at: str = Field(
        validation_alias=AliasChoices("meal_occurred_at", "mealOccurredAt"),
        serialization_alias="mealOccurredAt",
    )
    status: str
    source_type: str = Field(
        validation_alias=AliasChoices("source_type", "sourceType"),
        serialization_alias="sourceType",
    )
    is_manual: bool = Field(
        validation_alias=AliasChoices("is_manual", "isManual"),
        serialization_alias="isManual",
    )
    idempotency_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("idempotency_key", "idempotencyKey"),
        serialization_alias="idempotencyKey",
    )
    session_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("session_id", "sessionId"),
        serialization_alias="sessionId",
    )
    source_message_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("source_message_id", "sourceMessageId"),
        serialization_alias="sourceMessageId",
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

    food_log_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("food_log_id", "foodLogId"),
        serialization_alias="foodLogId",
    )
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
    meal_occurred_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("meal_occurred_at", "mealOccurredAt"),
        serialization_alias="mealOccurredAt",
    )
    status: str | None = None
    idempotency_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("idempotency_key", "idempotencyKey"),
        serialization_alias="idempotencyKey",
    )
    is_manual: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("is_manual", "isManual"),
        serialization_alias="isManual",
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

    @field_validator("food_log_id", "session_id", "source_message_id")
    @classmethod
    def validate_positive_ids(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("identifier must be greater than 0")
        return value

    @field_validator("meal_occurred_at")
    @classmethod
    def validate_meal_occurred_at(cls, value: str | None) -> str | None:
        return _normalize_timestamp_string(value)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in {"active", "deleted"}:
            raise ValueError("status must be active or deleted")
        return normalized

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class FoodLogPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    meal_description: str | None = Field(
        default=None,
        validation_alias=AliasChoices("meal_description", "mealDescription"),
        serialization_alias="mealDescription",
    )
    result_title: str | None = Field(
        default=None,
        validation_alias=AliasChoices("result_title", "resultTitle"),
        serialization_alias="resultTitle",
    )
    result_confidence: str | None = Field(
        default=None,
        validation_alias=AliasChoices("result_confidence", "resultConfidence"),
        serialization_alias="resultConfidence",
    )
    result_description: str | None = Field(
        default=None,
        validation_alias=AliasChoices("result_description", "resultDescription"),
        serialization_alias="resultDescription",
    )
    total_calories: str | None = Field(
        default=None,
        validation_alias=AliasChoices("total_calories", "totalCalories", "total"),
        serialization_alias="totalCalories",
    )
    ingredients: list[EstimateItem] | None = None
    assistant_suggestion: str | None = Field(
        default=None,
        validation_alias=AliasChoices("assistant_suggestion", "assistantSuggestion"),
        serialization_alias="assistantSuggestion",
    )
    meal_occurred_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("meal_occurred_at", "mealOccurredAt"),
        serialization_alias="mealOccurredAt",
    )

    @field_validator(
        "meal_description",
        "result_title",
        "result_confidence",
        "result_description",
        "total_calories",
        "assistant_suggestion",
    )
    @classmethod
    def validate_patch_text_fields(cls, value: str | None, info) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        if normalized:
            return normalized
        raise ValueError(f"{info.field_name} cannot be empty")

    @field_validator("meal_occurred_at")
    @classmethod
    def validate_patch_meal_occurred_at(cls, value: str | None) -> str | None:
        return _normalize_timestamp_string(value)

    @model_validator(mode="after")
    def validate_patch_has_changes(self) -> "FoodLogPatchRequest":
        if not any(
            getattr(self, field_name) is not None
            for field_name in (
                "meal_description",
                "result_title",
                "result_confidence",
                "result_description",
                "total_calories",
                "ingredients",
                "assistant_suggestion",
                "meal_occurred_at",
            )
        ):
            raise ValueError("at least one field must be provided")
        return self


class FoodLogFromEstimateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    meal_description: str = Field(
        validation_alias=AliasChoices("meal_description", "mealDescription"),
        serialization_alias="mealDescription",
    )
    estimate: EstimateResult
    client_request_id: str = Field(
        validation_alias=AliasChoices(
            "client_request_id",
            "clientRequestId",
            "idempotency_key",
            "idempotencyKey",
        ),
        serialization_alias="clientRequestId",
    )
    meal_occurred_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("meal_occurred_at", "mealOccurredAt"),
        serialization_alias="mealOccurredAt",
    )

    @field_validator("meal_description")
    @classmethod
    def validate_meal_description(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if normalized:
            return normalized
        raise ValueError("meal_description cannot be empty")

    @field_validator("client_request_id")
    @classmethod
    def validate_client_request_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("client_request_id cannot be empty")
        if len(normalized) > 128:
            raise ValueError("client_request_id cannot exceed 128 characters")
        return normalized

    @field_validator("meal_occurred_at")
    @classmethod
    def validate_from_estimate_meal_occurred_at(cls, value: str | None) -> str | None:
        return _normalize_timestamp_string(value)


class FoodLogFromEstimateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    client_request_id: str = Field(
        validation_alias=AliasChoices("client_request_id", "clientRequestId"),
        serialization_alias="clientRequestId",
    )
    food_log_id: str = Field(
        validation_alias=AliasChoices("food_log_id", "foodLogId"),
        serialization_alias="foodLogId",
    )
    save_status: Literal["saved"] = Field(
        default="saved",
        validation_alias=AliasChoices("save_status", "saveStatus"),
        serialization_alias="saveStatus",
    )
    food_log: FoodLogEntryOut = Field(
        validation_alias=AliasChoices("food_log", "foodLog"),
        serialization_alias="foodLog",
    )


def serialize_food_log_entry(entry: dict[str, object]) -> FoodLogEntryOut:
    saved_at = _resolve_saved_at_value(entry)
    meal_occurred_at = _resolve_meal_occurred_at_value(entry, saved_at)
    timestamp = _parse_timestamp(meal_occurred_at)

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
            "meal_occurred_at": meal_occurred_at,
            "status": entry["status"],
            "source_type": entry["source_type"],
            "is_manual": bool(entry["is_manual"]),
            "idempotency_key": entry.get("idempotency_key"),
            "session_id": (
                str(entry["session_id"])
                if entry.get("session_id") is not None
                else None
            ),
            "source_message_id": (
                str(entry["source_message_id"])
                if entry.get("source_message_id") is not None
                else None
            ),
        }
    )


def serialize_food_log_from_estimate_response(
    entry: dict[str, object],
    *,
    client_request_id: str,
) -> FoodLogFromEstimateResponse:
    food_log = serialize_food_log_entry(entry)
    return FoodLogFromEstimateResponse(
        client_request_id=client_request_id,
        food_log_id=food_log.id,
        save_status="saved",
        food_log=food_log,
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


def _resolve_meal_occurred_at_value(entry: dict[str, object], fallback: str) -> str:
    value = entry.get("meal_occurred_at")
    if isinstance(value, str) and value.strip():
        return value
    return fallback


def _parse_timestamp(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
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


def _normalize_timestamp_string(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    normalized_value = normalized.replace("T", " ")
    try:
        timestamp = datetime.strptime(normalized_value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            timestamp = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(
                "meal_occurred_at must be ISO datetime or YYYY-MM-DD HH:MM:SS"
            ) from exc
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")
