from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class EstimateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    query: str
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

    @field_validator("name", "portion", "energy")
    @classmethod
    def validate_text_field(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("\u5b57\u6bb5\u4e0d\u80fd\u4e3a\u7a7a")
        return normalized


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


class EstimateErrorField(BaseModel):
    field: str
    message: str


class EstimateError(BaseModel):
    code: str
    message: str
    fields: list[EstimateErrorField] | None = None
    retryable: bool


class EstimateResponse(BaseModel):
    success: bool
    data: EstimateResult | None = None
    error: EstimateError | None = None
