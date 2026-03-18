from datetime import date
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator, model_validator


class InsightsDateRange(BaseModel):
    model_config = ConfigDict(extra="forbid")

    start: date
    end: date

    @model_validator(mode="after")
    def validate_range(self) -> "InsightsDateRange":
        if self.end < self.start:
            raise ValueError("end 不能早于 start")
        return self


class InsightsAnalyzeRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    user_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("user_id", "userId"),
        serialization_alias="userId",
    )
    mode: Literal["day", "week"]
    selected_log_ids: list[int] | None = Field(
        default=None,
        validation_alias=AliasChoices("selected_log_ids", "selectedLogIds"),
        serialization_alias="selectedLogIds",
    )
    date_range: InsightsDateRange = Field(
        validation_alias=AliasChoices("date_range", "dateRange"),
        serialization_alias="dateRange",
    )

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("userId 必须大于 0")
        return value

    @field_validator("selected_log_ids")
    @classmethod
    def validate_selected_log_ids(cls, value: list[int] | None) -> list[int] | None:
        if value is None:
            return None
        if not value:
            raise ValueError("selectedLogIds 不能为空数组，请传 null 或省略")
        for log_id in value:
            if log_id <= 0:
                raise ValueError("selectedLogIds 中的 id 必须大于 0")
        return value


class NutritionAggregation(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    total_calories: float = Field(serialization_alias="totalCalories")
    total_protein: float = Field(serialization_alias="totalProtein")
    total_carbs: float = Field(serialization_alias="totalCarbs")
    total_fat: float = Field(serialization_alias="totalFat")
    protein_ratio: float = Field(serialization_alias="proteinRatio")
    carbs_ratio: float = Field(serialization_alias="carbsRatio")
    fat_ratio: float = Field(serialization_alias="fatRatio")
    entry_count: int = Field(serialization_alias="entryCount")


class InsightsEntryBrief(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str
    name: str
    calories: str
    date: str
    time: str


class AIInsights(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    risks: list[str]
    actions: list[str]


class InsightsAnalyzeData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    aggregation: NutritionAggregation
    entries: list[InsightsEntryBrief]
    ai: AIInsights


class InsightsError(BaseModel):
    code: str
    message: str
    retryable: bool


class InsightsAnalyzeResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    success: bool
    data: InsightsAnalyzeData | None = None
    error: InsightsError | None = None
