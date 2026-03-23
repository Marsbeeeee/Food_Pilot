from pydantic import BaseModel, ConfigDict, field_validator
from backend.schemas.knowledge import KnowledgeReference


class GuidanceReply(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    description: str
    response: str
    knowledge_refs: list[KnowledgeReference] | None = None

    @field_validator("title", "description", "response")
    @classmethod
    def validate_text_field(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("field cannot be empty")
        return normalized
