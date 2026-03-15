from pydantic import BaseModel, ConfigDict, field_validator


class GuidanceReply(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str
    response: str

    @field_validator("title", "description", "response")
    @classmethod
    def validate_text_field(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("field cannot be empty")
        return normalized
