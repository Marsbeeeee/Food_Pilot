from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator

from backend.schemas.user import UserOut, normalize_email


class RegisterRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    email: str
    password: str
    display_name: str = Field(
        validation_alias=AliasChoices("display_name", "displayName"),
        serialization_alias="displayName",
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        normalized = value.strip()
        if len(normalized) < 8:
            raise ValueError("password must be at least 8 characters")
        return normalized

    @field_validator("display_name")
    @classmethod
    def validate_display_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("display_name cannot be empty")
        return normalized


class LoginRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    email: str
    password: str

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        return normalize_email(value)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("password cannot be empty")
        return normalized


class AuthResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    access_token: str = Field(
        validation_alias=AliasChoices("access_token", "accessToken"),
        serialization_alias="accessToken",
    )
    token_type: str = Field(
        default="bearer",
        validation_alias=AliasChoices("token_type", "tokenType"),
        serialization_alias="tokenType",
    )
    user: UserOut
