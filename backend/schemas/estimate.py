from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class EstimateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    query: str

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("Query cannot be empty")
        if len(normalized) < 2:
            raise ValueError("Query must be at least 2 characters")
        if len(normalized) > 500:
            raise ValueError("Query must be 500 characters or fewer")
        return normalized


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
            raise ValueError("Item fields cannot be empty")
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
