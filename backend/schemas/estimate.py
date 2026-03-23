from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator
from backend.schemas.knowledge import KnowledgeReference


class EstimateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    query: str
    client_request_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("client_request_id", "clientRequestId"),
        serialization_alias="clientRequestId",
    )
    profile_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("profile_id", "profileId"),
        serialization_alias="profileId",
    )
    session_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("session_id", "sessionId"),
        serialization_alias="sessionId",
    )

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("\u8f93\u5165\u5185\u5bb9\u4e0d\u80fd\u4e3a\u7a7a")
        if len(normalized) < 2:
            raise ValueError("\u8bf7\u81f3\u5c11\u8f93\u5165 2 \u4e2a\u5b57\u7b26")
        if len(normalized) > 500:
            raise ValueError("\u8f93\u5165\u5185\u5bb9\u4e0d\u80fd\u8d85\u8fc7 500 \u4e2a\u5b57\u7b26")
        return normalized

    @field_validator("client_request_id")
    @classmethod
    def validate_client_request_id(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        if not normalized:
            raise ValueError("client_request_id cannot be empty")
        if len(normalized) > 128:
            raise ValueError("client_request_id cannot exceed 128 characters")
        return normalized

    @field_validator("profile_id")
    @classmethod
    def validate_profile_id(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("profile_id \u5fc5\u987b\u5927\u4e8e 0")
        return value

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("session_id \u5fc5\u987b\u5927\u4e8e 0")
        return value


class EstimateItem(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    portion: str
    energy: str
    protein: str | None = None
    carbs: str | None = None
    fat: str | None = None
    description: str | None = None

    @field_validator("name", "portion", "energy")
    @classmethod
    def validate_text_field(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("\u5b57\u6bb5\u4e0d\u80fd\u4e3a\u7a7a")
        return normalized

    @field_validator("protein", "carbs", "fat", "description", mode="before")
    @classmethod
    def validate_macro_field(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None


class EstimateResult(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    title: str
    description: str
    confidence: str
    items: list[EstimateItem]
    total_calories: str = Field(
        alias="totalCalories",
        serialization_alias="total_calories",
        validation_alias=AliasChoices("total_calories", "totalCalories", "total"),
    )
    suggestion: str
    itemization_mode: str | None = Field(
        default=None,
        validation_alias=AliasChoices("itemization_mode", "itemizationMode"),
        serialization_alias="itemization_mode",
    )
    knowledge_refs: list[KnowledgeReference] | None = Field(
        default=None,
        validation_alias=AliasChoices("knowledge_refs", "knowledgeRefs"),
        serialization_alias="knowledge_refs",
    )


class EstimateErrorField(BaseModel):
    field: str
    message: str


class EstimateError(BaseModel):
    code: str
    message: str
    fields: list[EstimateErrorField] | None = None
    retryable: bool


class EstimateResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    data: EstimateResult | None = None
    error: EstimateError | None = None
    client_request_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("client_request_id", "clientRequestId"),
        serialization_alias="clientRequestId",
    )
    food_log_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("food_log_id", "foodLogId"),
        serialization_alias="foodLogId",
    )
    save_status: Literal["saved", "not_saved"] = Field(
        default="not_saved",
        validation_alias=AliasChoices("save_status", "saveStatus"),
        serialization_alias="saveStatus",
    )
