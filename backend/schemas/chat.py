import json

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from backend.schemas.estimate import EstimateItem


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


class ChatMessageOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: int
    session_id: int = Field(
        validation_alias=AliasChoices("session_id", "sessionId"),
        serialization_alias="sessionId",
    )
    role: str
    message_type: str = Field(
        validation_alias=AliasChoices("message_type", "messageType"),
        serialization_alias="messageType",
    )
    content: str | None = None
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
