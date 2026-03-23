import json
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator

from backend.schemas.estimate import EstimateItem
from backend.schemas.knowledge import KnowledgeReference


ChatMessageType = Literal["text", "meal_estimate", "meal_recommendation"]

LEGACY_CHAT_MESSAGE_TYPE_MAP = {
    "estimate_result": "meal_estimate",
}


class ChatSendMessageRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    content: str
    profile_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("profile_id", "profileId"),
        serialization_alias="profileId",
    )

    @field_validator("content")
    @classmethod
    def validate_content(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("content cannot be empty")
        if len(normalized) < 2:
            raise ValueError("content must be at least 2 characters")
        if len(normalized) > 500:
            raise ValueError("content must be 500 characters or fewer")
        return normalized

    @field_validator("profile_id")
    @classmethod
    def validate_profile_id(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("profile_id must be greater than 0")
        return value


class RenameSessionRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    title: str

    @field_validator("title")
    @classmethod
    def validate_title(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if not normalized:
            raise ValueError("title cannot be empty")
        if len(normalized) > 120:
            raise ValueError("title must be 120 characters or fewer")
        return normalized


class EstimateBlockPayload(BaseModel):
    """Single food estimate block when multiple foods are present."""

    model_config = ConfigDict(extra="forbid")

    title: str
    confidence: str | None = None
    description: str | None = None
    items: list[EstimateItem]
    total: str


class ChatMessagePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    text: str | None = None
    title: str | None = None
    confidence: str | None = None
    description: str | None = None
    items: list[EstimateItem] | None = None
    total: str | None = None
    estimates: list[EstimateBlockPayload] | None = None
    suggestion: str | None = None
    knowledge_refs: list[KnowledgeReference] | None = None


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: int
    session_id: int = Field(
        validation_alias=AliasChoices("session_id", "sessionId"),
        serialization_alias="sessionId",
    )
    role: str
    message_type: ChatMessageType = Field(
        validation_alias=AliasChoices("message_type", "messageType"),
        serialization_alias="messageType",
    )
    content: str | None = None
    payload: ChatMessagePayload | None = None
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
    result_items: list[EstimateItem] | None = Field(
        default=None,
        validation_alias=AliasChoices("result_items", "resultItems"),
        serialization_alias="resultItems",
    )
    result_total: str | None = Field(
        default=None,
        validation_alias=AliasChoices("result_total", "resultTotal"),
        serialization_alias="resultTotal",
    )
    created_at: str = Field(
        validation_alias=AliasChoices("created_at", "createdAt"),
        serialization_alias="createdAt",
    )

    @model_validator(mode="before")
    @classmethod
    def normalize_contract(cls, value: object) -> object:
        if not isinstance(value, dict):
            return value

        data = dict(value)
        normalized_message_type = _normalize_message_type(
            _get_first_present(data, "message_type", "messageType")
        )
        data.pop("messageType", None)
        data["message_type"] = normalized_message_type

        if _get_first_present(data, "payload") is None:
            payload = _build_payload_from_legacy_fields(data, normalized_message_type)
            if payload is not None:
                data["payload"] = payload

        return data

    @field_validator("message_type", mode="before")
    @classmethod
    def validate_message_type(cls, value: object) -> ChatMessageType:
        return _normalize_message_type(value)


class ChatSessionSummary(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: int
    title: str
    created_at: str = Field(
        validation_alias=AliasChoices("created_at", "createdAt"),
        serialization_alias="createdAt",
    )
    updated_at: str = Field(
        validation_alias=AliasChoices("updated_at", "updatedAt"),
        serialization_alias="updatedAt",
    )
    last_message_at: str = Field(
        validation_alias=AliasChoices("last_message_at", "lastMessageAt"),
        serialization_alias="lastMessageAt",
    )


class ChatSessionDetail(ChatSessionSummary):
    messages: list[ChatMessageOut]


class ChatMessageExchangeResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    session: ChatSessionSummary
    user_message: ChatMessageOut = Field(
        validation_alias=AliasChoices("user_message", "userMessage"),
        serialization_alias="userMessage",
    )
    assistant_message: ChatMessageOut = Field(
        validation_alias=AliasChoices("assistant_message", "assistantMessage"),
        serialization_alias="assistantMessage",
    )


def parse_result_items(value: str | None) -> list[EstimateItem] | None:
    if value is None:
        return None

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, list):
        return None

    return [EstimateItem.model_validate(item) for item in parsed]


def _normalize_message_type(value: object) -> ChatMessageType:
    if not isinstance(value, str):
        raise ValueError("message_type must be a string")

    normalized = LEGACY_CHAT_MESSAGE_TYPE_MAP.get(value, value)
    if normalized in {"text", "meal_estimate", "meal_recommendation"}:
        return normalized

    raise ValueError("message_type must be one of: text, meal_estimate, meal_recommendation")


def _build_payload_from_legacy_fields(
    data: dict[str, object],
    message_type: ChatMessageType,
) -> dict[str, object] | None:
    if message_type == "text":
        content = _get_first_present(data, "content")
        if isinstance(content, str) and content:
            return {"text": content}
        return None

    payload = {
        "title": _get_first_present(data, "result_title", "resultTitle"),
        "confidence": _get_first_present(data, "result_confidence", "resultConfidence"),
        "description": _get_first_present(data, "result_description", "resultDescription"),
        "items": _get_first_present(data, "result_items", "resultItems"),
        "total": _get_first_present(data, "result_total", "resultTotal"),
    }
    normalized_payload = {key: value for key, value in payload.items() if value is not None}
    return normalized_payload or None


def _get_first_present(data: dict[str, object], *keys: str) -> object | None:
    for key in keys:
        if key in data:
            return data[key]
    return None
