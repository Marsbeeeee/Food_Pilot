from pydantic import BaseModel, ConfigDict, field_validator


class KnowledgeReference(BaseModel):
    model_config = ConfigDict(extra="forbid")

    food_name: str
    source_id: str
    source_name: str
    note: str | None = None
    updated_at: str | None = None

    @field_validator("food_name", "source_id", "source_name")
    @classmethod
    def validate_required_text(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("field cannot be empty")
        return normalized

    @field_validator("note", "updated_at", mode="before")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = str(value).strip()
        return normalized or None
