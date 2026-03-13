import json

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from backend.schemas.estimate import EstimateItem


class FoodLogEntryOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: int
    source_type: str = Field(
        validation_alias=AliasChoices("source_type", "sourceType"),
        serialization_alias="sourceType",
    )
    session_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("session_id", "sessionId"),
        serialization_alias="sessionId",
    )
    source_message_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("source_message_id", "sourceMessageId", "message_id", "messageId"),
        serialization_alias="sourceMessageId",
    )
    meal_description: str = Field(
        validation_alias=AliasChoices("meal_description", "mealDescription"),
        serialization_alias="mealDescription",
    )
    logged_at: str = Field(
        validation_alias=AliasChoices("logged_at", "loggedAt"),
        serialization_alias="loggedAt",
    )
    title: str
    confidence: str | None = None
    description: str
    items: list[EstimateItem] = Field(
        validation_alias=AliasChoices("items", "result_items"),
        serialization_alias="items",
    )
    total: str
    suggestion: str | None = None
    created_at: str = Field(
        validation_alias=AliasChoices("created_at", "createdAt"),
        serialization_alias="createdAt",
    )
    updated_at: str = Field(
        validation_alias=AliasChoices("updated_at", "updatedAt"),
        serialization_alias="updatedAt",
    )


def parse_food_log_items(value: str) -> list[EstimateItem]:
    parsed = json.loads(value)
    if not isinstance(parsed, list):
        raise ValueError("items_json must decode to a list")
    return [EstimateItem.model_validate(item) for item in parsed]
