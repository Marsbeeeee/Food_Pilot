import json

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class ProfileBase(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    age: int
    height: float
    weight: float
    sex: str
    activity_level: str = Field(
        validation_alias=AliasChoices("activity_level", "activityLevel"),
        serialization_alias="activityLevel",
    )
    goal: str
    kcal_target: int = Field(
        validation_alias=AliasChoices("kcal_target", "kcalTarget"),
        serialization_alias="kcalTarget",
    )
    diet_style: str = Field(
        validation_alias=AliasChoices("diet_style", "dietStyle"),
        serialization_alias="dietStyle",
    )
    allergies: list[str] = Field(default_factory=list)
    exercise_type: str = Field(
        validation_alias=AliasChoices("exercise_type", "exerciseType"),
        serialization_alias="exerciseType",
    )
    pace: str

    @field_validator(
        "sex",
        "activity_level",
        "goal",
        "diet_style",
        "exercise_type",
        "pace",
    )
    @classmethod
    def validate_text_fields(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("字段不能为空")
        return normalized

    @field_validator("allergies", mode="before")
    @classmethod
    def normalize_allergies(cls, value: object) -> list[str]:
        if value in (None, ""):
            return []
        if isinstance(value, list):
            return value
        if isinstance(value, str):
            normalized = value.strip()
            if not normalized:
                return []
            try:
                parsed = json.loads(normalized)
            except json.JSONDecodeError:
                return [item.strip() for item in normalized.split(",") if item.strip()]
            if isinstance(parsed, list):
                return parsed
        raise ValueError("allergies 必须为字符串数组")

    @field_validator("allergies")
    @classmethod
    def validate_allergies(cls, value: list[str]) -> list[str]:
        normalized: list[str] = []
        for item in value:
            if not isinstance(item, str):
                raise ValueError("allergies 必须为字符串数组")
            cleaned = item.strip()
            if cleaned:
                normalized.append(cleaned)
        return normalized


class ProfileIn(ProfileBase):
    pass


class ProfileOut(ProfileBase):
    id: int
