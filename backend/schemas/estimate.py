from pydantic import BaseModel, ConfigDict, field_validator


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
    name: str
    portion: str
    energy: str


class EstimateResult(BaseModel):
    title: str
    description: str
    confidence: str
    items: list[EstimateItem]
    totalCalories: str
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
