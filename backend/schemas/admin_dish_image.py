from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


class AdminDishImageListQuery(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    status: str | None = None
    query: str | None = None
    created_from: str | None = Field(
        default=None,
        validation_alias=AliasChoices("created_from", "createdFrom"),
        serialization_alias="createdFrom",
    )
    created_to: str | None = Field(
        default=None,
        validation_alias=AliasChoices("created_to", "createdTo"),
        serialization_alias="createdTo",
    )
    limit: int = 50

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in {"pending", "approved", "rejected"}:
            raise ValueError("status must be pending, approved, or rejected")
        return normalized

    @field_validator("query", "created_from", "created_to")
    @classmethod
    def normalize_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, value: int) -> int:
        if value < 1 or value > 200:
            raise ValueError("limit must be between 1 and 200")
        return value


class AdminDishImageActionRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    note: str | None = None

    @field_validator("note")
    @classmethod
    def normalize_note(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class AdminDishImageGenerationJobListQuery(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    limit: int = 50

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, value: int) -> int:
        if value < 1 or value > 200:
            raise ValueError("limit must be between 1 and 200")
        return value


class AdminDishImageActorOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: int
    display_name: str = Field(
        validation_alias=AliasChoices("display_name", "displayName"),
        serialization_alias="displayName",
    )
    email: str


class AdminDishImageOperationOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: int
    dish_image_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("dish_image_id", "dishImageId"),
        serialization_alias="dishImageId",
    )
    action: str
    result_status: str = Field(
        validation_alias=AliasChoices("result_status", "resultStatus"),
        serialization_alias="resultStatus",
    )
    note: str | None = None
    created_at: str = Field(
        validation_alias=AliasChoices("created_at", "createdAt"),
        serialization_alias="createdAt",
    )
    actor: AdminDishImageActorOut


class AdminDishImageActiveGenerationJobOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: int
    status: str
    created_at: str = Field(
        validation_alias=AliasChoices("created_at", "createdAt"),
        serialization_alias="createdAt",
    )
    started_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("started_at", "startedAt"),
        serialization_alias="startedAt",
    )


class AdminDishImageGenerationJobOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: int
    standard_dish_id: int = Field(
        validation_alias=AliasChoices("standard_dish_id", "standardDishId"),
        serialization_alias="standardDishId",
    )
    standard_dish_name: str = Field(
        validation_alias=AliasChoices("standard_dish_name", "standardDishName"),
        serialization_alias="standardDishName",
    )
    status: str
    created_at: str = Field(
        validation_alias=AliasChoices("created_at", "createdAt"),
        serialization_alias="createdAt",
    )
    started_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("started_at", "startedAt"),
        serialization_alias="startedAt",
    )


class AdminDishImageListItemOut(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    id: int
    standard_dish_id: int = Field(
        validation_alias=AliasChoices("standard_dish_id", "standardDishId"),
        serialization_alias="standardDishId",
    )
    standard_dish_name: str = Field(
        validation_alias=AliasChoices("standard_dish_name", "standardDishName"),
        serialization_alias="standardDishName",
    )
    image_url: str = Field(
        validation_alias=AliasChoices("image_url", "imageUrl"),
        serialization_alias="imageUrl",
    )
    status: str
    prompt_version: str | None = Field(
        default=None,
        validation_alias=AliasChoices("prompt_version", "promptVersion"),
        serialization_alias="promptVersion",
    )
    review_note: str | None = Field(
        default=None,
        validation_alias=AliasChoices("review_note", "reviewNote"),
        serialization_alias="reviewNote",
    )
    created_at: str = Field(
        validation_alias=AliasChoices("created_at", "createdAt"),
        serialization_alias="createdAt",
    )
    reviewed_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("reviewed_at", "reviewedAt"),
        serialization_alias="reviewedAt",
    )
    official_image_url: str | None = Field(
        default=None,
        validation_alias=AliasChoices("official_image_url", "officialImageUrl"),
        serialization_alias="officialImageUrl",
    )
    official_image_status: str | None = Field(
        default=None,
        validation_alias=AliasChoices("official_image_status", "officialImageStatus"),
        serialization_alias="officialImageStatus",
    )
    is_current_official: bool = Field(
        validation_alias=AliasChoices("is_current_official", "isCurrentOfficial"),
        serialization_alias="isCurrentOfficial",
    )
    active_generation_job: AdminDishImageActiveGenerationJobOut | None = Field(
        default=None,
        validation_alias=AliasChoices("active_generation_job", "activeGenerationJob"),
        serialization_alias="activeGenerationJob",
    )


class AdminDishImageDetailOut(AdminDishImageListItemOut):
    official_image_prompt_version: str | None = Field(
        default=None,
        validation_alias=AliasChoices("official_image_prompt_version", "officialImagePromptVersion"),
        serialization_alias="officialImagePromptVersion",
    )
    official_image_updated_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("official_image_updated_at", "officialImageUpdatedAt"),
        serialization_alias="officialImageUpdatedAt",
    )
    can_approve: bool = Field(
        validation_alias=AliasChoices("can_approve", "canApprove"),
        serialization_alias="canApprove",
    )
    can_reject: bool = Field(
        validation_alias=AliasChoices("can_reject", "canReject"),
        serialization_alias="canReject",
    )
    can_regenerate: bool = Field(
        validation_alias=AliasChoices("can_regenerate", "canRegenerate"),
        serialization_alias="canRegenerate",
    )
    recent_operations: list[AdminDishImageOperationOut] = Field(
        validation_alias=AliasChoices("recent_operations", "recentOperations"),
        serialization_alias="recentOperations",
    )
