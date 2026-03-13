from datetime import datetime

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


def normalize_email(value: str) -> str:
    normalized = value.strip().lower()
    local_part, separator, domain = normalized.partition("@")
    if not separator or not local_part or not domain or "." not in domain:
        raise ValueError("email must be a valid email address")
    return normalized


class UserBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    email: str
    display_name: str = Field(
        validation_alias=AliasChoices("display_name", "displayName"),
        serialization_alias="displayName",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("display_name cannot be empty")
        return normalized


class UserCreate(UserBase):
    password_hash: str = Field(
        validation_alias=AliasChoices("password_hash", "passwordHash"),
        serialization_alias="passwordHash",
    )

    @field_validator("password_hash")
    @classmethod
    def validate_password_hash(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("password_hash cannot be empty")
        return normalized


class UserOut(UserBase):
    id: int
    created_at: datetime = Field(
        validation_alias=AliasChoices("created_at", "createdAt"),
        serialization_alias="createdAt",
    )
    updated_at: datetime = Field(
        validation_alias=AliasChoices("updated_at", "updatedAt"),
        serialization_alias="updatedAt",
    )
