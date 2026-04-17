import json
import re
from datetime import date, datetime
from hashlib import sha1
from typing import Literal

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)

from backend.schemas.decision_card import DecisionCard
from backend.schemas.estimate import EstimateItem, EstimateResult


MONTH_ABBREVIATIONS = (
    "Jan",
    "Feb",
    "Mar",
    "Apr",
    "May",
    "Jun",
    "Jul",
    "Aug",
    "Sep",
    "Oct",
    "Nov",
    "Dec",
)

PRIMARY_CATEGORY_DEFINITIONS = (
    {
        "id": "beverage",
        "name": "饮品",
        "sort_order": 10,
        "category_names": {"现制茶饮", "咖啡饮品", "通用饮品"},
        "keywords": ("奶茶", "茶饮", "果茶", "咖啡", "拿铁", "美式", "摩卡", "澳白", "生椰"),
    },
    {
        "id": "hot_pot",
        "name": "火锅",
        "sort_order": 20,
        "category_names": {"火锅"},
        "keywords": ("火锅", "串串", "冒菜", "毛肚", "鸭肠", "麻辣香锅", "关东煮"),
    },
    {
        "id": "bbq_grill",
        "name": "烧烤烤肉",
        "sort_order": 30,
        "category_names": {"烧烤烤肉"},
        "keywords": ("烧烤", "烤肉", "烤串", "bbq"),
    },
    {
        "id": "bakery_dessert",
        "name": "面包甜点",
        "sort_order": 40,
        "category_names": {"甜品蛋糕"},
        "keywords": ("蛋糕", "甜品", "布丁", "冰淇淋", "提拉米苏", "甜甜圈", "面包", "泡芙"),
    },
    {
        "id": "light_salad",
        "name": "轻食沙拉",
        "sort_order": 50,
        "category_names": {"轻食沙拉"},
        "keywords": ("沙拉", "轻食", "poke", "poke bowl", "健身餐", "低脂餐"),
    },
    {
        "id": "regional_chinese",
        "name": "地方菜系",
        "sort_order": 60,
        "category_names": {"地方菜系"},
        "keywords": (
            "川菜",
            "湘菜",
            "粤菜",
            "粤式",
            "东北菜",
            "云南菜",
            "江浙菜",
            "本帮",
            "烧腊",
            "淮扬",
            "闽菜",
            "鲁菜",
        ),
    },
    {
        "id": "international_cuisine",
        "name": "异域料理",
        "sort_order": 70,
        "category_names": {"日式料理", "韩式料理", "西餐"},
        "keywords": (
            "寿司",
            "刺身",
            "日式",
            "丼",
            "乌冬",
            "天妇罗",
            "韩式",
            "石锅拌饭",
            "泡菜",
            "部队锅",
            "意面",
            "牛排",
            "泰式",
            "越南",
            "墨西哥",
        ),
    },
    {
        "id": "fast_food_snack",
        "name": "小吃快餐",
        "sort_order": 80,
        "category_names": {"西式快餐", "饭类主食", "面食主食", "小吃简餐"},
        "keywords": (
            "汉堡",
            "薯条",
            "炸鸡",
            "盖饭",
            "炒饭",
            "拌饭",
            "米饭",
            "米线",
            "面",
            "粉",
            "拉面",
            "饺子",
            "煎饼",
            "麻辣烫",
            "卤味",
            "简餐",
            "便当",
            "卷饼",
        ),
    },
    {
        "id": "grocery_snack",
        "name": "生鲜零食",
        "sort_order": 90,
        "category_names": {"食品生鲜"},
        "keywords": ("生鲜", "水果", "酸奶", "牛奶", "零食", "坚果", "能量棒", "饼干"),
    },
)

DEFAULT_PRIMARY_CATEGORY = {
    "id": "other",
    "name": "其他",
    "sort_order": 999,
}

HOMEMADE_MARKERS = ("自制", "自家", "homemade", "home made")


class FoodLogPrimaryCategoryOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str
    name: str
    cover: str | None = None
    sort_order: int | None = Field(
        default=None,
        validation_alias=AliasChoices("sort_order", "sortOrder"),
        serialization_alias="sortOrder",
    )


class FoodLogBrandGroupOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str
    name: str
    type: str
    logo: str | None = None
    sort_order: int | None = Field(
        default=None,
        validation_alias=AliasChoices("sort_order", "sortOrder"),
        serialization_alias="sortOrder",
    )


class FoodLogEntryOut(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    id: str
    name: str
    description: str
    calories: str
    date: str
    time: str
    breakdown: list[EstimateItem]
    image: str | None = None
    image_source: str | None = Field(
        default=None,
        validation_alias=AliasChoices("image_source", "imageSource"),
        serialization_alias="imageSource",
    )
    image_license: str | None = Field(
        default=None,
        validation_alias=AliasChoices("image_license", "imageLicense"),
        serialization_alias="imageLicense",
    )
    decision_card: DecisionCard | None = Field(
        default=None,
        validation_alias=AliasChoices("decision_card", "decisionCard"),
        serialization_alias="decisionCard",
    )
    category: FoodLogPrimaryCategoryOut
    brand_group: FoodLogBrandGroupOut = Field(
        validation_alias=AliasChoices("brand_group", "brandGroup"),
        serialization_alias="brandGroup",
    )
    standard_dish_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("standard_dish_id", "standardDishId"),
        serialization_alias="standardDishId",
    )
    standard_dish_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("standard_dish_name", "standardDishName"),
        serialization_alias="standardDishName",
    )
    protein: str | None = None
    carbs: str | None = None
    fat: str | None = None
    saved_at: str = Field(
        validation_alias=AliasChoices("saved_at", "savedAt"),
        serialization_alias="savedAt",
    )
    meal_occurred_at: str = Field(
        validation_alias=AliasChoices("meal_occurred_at", "mealOccurredAt"),
        serialization_alias="mealOccurredAt",
    )
    status: str
    source_type: str = Field(
        validation_alias=AliasChoices("source_type", "sourceType"),
        serialization_alias="sourceType",
    )
    is_manual: bool = Field(
        validation_alias=AliasChoices("is_manual", "isManual"),
        serialization_alias="isManual",
    )
    idempotency_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("idempotency_key", "idempotencyKey"),
        serialization_alias="idempotencyKey",
    )
    session_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("session_id", "sessionId"),
        serialization_alias="sessionId",
    )
    source_message_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("source_message_id", "sourceMessageId"),
        serialization_alias="sourceMessageId",
    )
    decision_card: DecisionCard | None = Field(
        default=None,
        validation_alias=AliasChoices("decision_card", "decisionCard"),
        serialization_alias="decisionCard",
    )


class FoodLogListQuery(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    session_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("session_id", "sessionId"),
        serialization_alias="sessionId",
    )
    limit: int | None = None
    date_from: date | None = Field(
        default=None,
        validation_alias=AliasChoices("date_from", "dateFrom"),
        serialization_alias="dateFrom",
    )
    date_to: date | None = Field(
        default=None,
        validation_alias=AliasChoices("date_to", "dateTo"),
        serialization_alias="dateTo",
    )
    query: str | None = Field(
        default=None,
        validation_alias=AliasChoices("query", "keyword", "meal"),
        serialization_alias="query",
    )
    source_type: Literal["estimate_api", "chat_message", "manual"] | None = Field(
        default=None,
        validation_alias=AliasChoices("source_type", "sourceType"),
        serialization_alias="sourceType",
    )
    has_image: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("has_image", "hasImage"),
        serialization_alias="hasImage",
    )
    sort: Literal["created_desc", "created_asc"] = Field(
        default="created_desc",
        validation_alias=AliasChoices("sort", "order"),
        serialization_alias="sort",
    )

    @field_validator("session_id")
    @classmethod
    def validate_session_id(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("session_id must be greater than 0")
        return value

    @field_validator("limit")
    @classmethod
    def validate_limit(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("limit must be greater than 0")
        return value

    @field_validator("query")
    @classmethod
    def validate_query(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        return normalized or None

    @field_validator("date_to")
    @classmethod
    def validate_date_range(cls, value: date | None, info) -> date | None:
        date_from = info.data.get("date_from")
        if value is not None and date_from is not None and value < date_from:
            raise ValueError("date_to cannot be earlier than date_from")
        return value


class FoodLogSaveRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    food_log_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("food_log_id", "foodLogId"),
        serialization_alias="foodLogId",
    )
    source_type: str = Field(
        validation_alias=AliasChoices("source_type", "sourceType"),
        serialization_alias="sourceType",
    )
    meal_description: str = Field(
        validation_alias=AliasChoices("meal_description", "mealDescription"),
        serialization_alias="mealDescription",
    )
    result_title: str = Field(
        validation_alias=AliasChoices("result_title", "resultTitle"),
        serialization_alias="resultTitle",
    )
    result_confidence: str | None = Field(
        default=None,
        validation_alias=AliasChoices("result_confidence", "resultConfidence"),
        serialization_alias="resultConfidence",
    )
    result_description: str = Field(
        validation_alias=AliasChoices("result_description", "resultDescription"),
        serialization_alias="resultDescription",
    )
    total_calories: str = Field(
        validation_alias=AliasChoices("total_calories", "totalCalories", "total"),
        serialization_alias="totalCalories",
    )
    ingredients: list[EstimateItem]
    session_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("session_id", "sessionId"),
        serialization_alias="sessionId",
    )
    source_message_id: int | None = Field(
        default=None,
        validation_alias=AliasChoices("source_message_id", "sourceMessageId"),
        serialization_alias="sourceMessageId",
    )
    assistant_suggestion: str | None = Field(
        default=None,
        validation_alias=AliasChoices("assistant_suggestion", "assistantSuggestion"),
        serialization_alias="assistantSuggestion",
    )
    meal_occurred_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("meal_occurred_at", "mealOccurredAt"),
        serialization_alias="mealOccurredAt",
    )
    status: str | None = None
    idempotency_key: str | None = Field(
        default=None,
        validation_alias=AliasChoices("idempotency_key", "idempotencyKey"),
        serialization_alias="idempotencyKey",
    )
    is_manual: bool | None = Field(
        default=None,
        validation_alias=AliasChoices("is_manual", "isManual"),
        serialization_alias="isManual",
    )
    image: str | None = Field(
        default=None,
        validation_alias=AliasChoices("image"),
        serialization_alias="image",
    )
    image_source: str | None = Field(
        default=None,
        validation_alias=AliasChoices("image_source", "imageSource"),
        serialization_alias="imageSource",
    )
    image_license: str | None = Field(
        default=None,
        validation_alias=AliasChoices("image_license", "imageLicense"),
        serialization_alias="imageLicense",
    )
    decision_card: DecisionCard | None = Field(
        default=None,
        validation_alias=AliasChoices("decision_card", "decisionCard"),
        serialization_alias="decisionCard",
    )

    @field_validator(
        "source_type",
        "meal_description",
        "result_title",
        "result_description",
        "total_calories",
        "assistant_suggestion",
    )
    @classmethod
    def validate_text_fields(cls, value: str | None, info) -> str | None:
        if value is None:
            return None

        normalized = " ".join(value.strip().split())
        if normalized:
            return normalized
        raise ValueError(f"{info.field_name} cannot be empty")

    @field_validator("food_log_id", "session_id", "source_message_id")
    @classmethod
    def validate_positive_ids(cls, value: int | None) -> int | None:
        if value is not None and value <= 0:
            raise ValueError("identifier must be greater than 0")
        return value

    @field_validator("meal_occurred_at")
    @classmethod
    def validate_meal_occurred_at(cls, value: str | None) -> str | None:
        return _normalize_timestamp_string(value)

    @field_validator("status")
    @classmethod
    def validate_status(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if normalized not in {"active", "deleted"}:
            raise ValueError("status must be active or deleted")
        return normalized

    @field_validator("idempotency_key")
    @classmethod
    def validate_idempotency_key(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip()
        return normalized or None


class FoodLogPatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    image: str | None = Field(
        default=None,
        validation_alias=AliasChoices("image"),
        serialization_alias="image",
    )
    image_source: str | None = Field(
        default=None,
        validation_alias=AliasChoices("image_source", "imageSource"),
        serialization_alias="imageSource",
    )
    image_license: str | None = Field(
        default=None,
        validation_alias=AliasChoices("image_license", "imageLicense"),
        serialization_alias="imageLicense",
    )
    meal_description: str | None = Field(
        default=None,
        validation_alias=AliasChoices("meal_description", "mealDescription"),
        serialization_alias="mealDescription",
    )
    result_title: str | None = Field(
        default=None,
        validation_alias=AliasChoices("result_title", "resultTitle"),
        serialization_alias="resultTitle",
    )
    result_confidence: str | None = Field(
        default=None,
        validation_alias=AliasChoices("result_confidence", "resultConfidence"),
        serialization_alias="resultConfidence",
    )
    result_description: str | None = Field(
        default=None,
        validation_alias=AliasChoices("result_description", "resultDescription"),
        serialization_alias="resultDescription",
    )
    total_calories: str | None = Field(
        default=None,
        validation_alias=AliasChoices("total_calories", "totalCalories", "total"),
        serialization_alias="totalCalories",
    )
    ingredients: list[EstimateItem] | None = None
    assistant_suggestion: str | None = Field(
        default=None,
        validation_alias=AliasChoices("assistant_suggestion", "assistantSuggestion"),
        serialization_alias="assistantSuggestion",
    )
    meal_occurred_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("meal_occurred_at", "mealOccurredAt"),
        serialization_alias="mealOccurredAt",
    )

    @field_validator(
        "meal_description",
        "result_title",
        "result_confidence",
        "result_description",
        "total_calories",
        "assistant_suggestion",
    )
    @classmethod
    def validate_patch_text_fields(cls, value: str | None, info) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        if normalized:
            return normalized
        raise ValueError(f"{info.field_name} cannot be empty")

    @field_validator("meal_occurred_at")
    @classmethod
    def validate_patch_meal_occurred_at(cls, value: str | None) -> str | None:
        return _normalize_timestamp_string(value)

    @model_validator(mode="after")
    def validate_patch_has_changes(self) -> "FoodLogPatchRequest":
        if not any(
            getattr(self, field_name) is not None
            for field_name in (
                "image",
                "image_source",
                "image_license",
                "meal_description",
                "result_title",
                "result_confidence",
                "result_description",
                "total_calories",
                "ingredients",
                "assistant_suggestion",
                "meal_occurred_at",
            )
        ):
            raise ValueError("at least one field must be provided")
        return self


class FoodLogFromEstimateRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    meal_description: str = Field(
        validation_alias=AliasChoices("meal_description", "mealDescription"),
        serialization_alias="mealDescription",
    )
    estimate: EstimateResult
    image: str | None = Field(
        default=None,
        validation_alias=AliasChoices("image"),
        serialization_alias="image",
    )
    image_source: str | None = Field(
        default=None,
        validation_alias=AliasChoices("image_source", "imageSource"),
        serialization_alias="imageSource",
    )
    image_license: str | None = Field(
        default=None,
        validation_alias=AliasChoices("image_license", "imageLicense"),
        serialization_alias="imageLicense",
    )
    client_request_id: str = Field(
        validation_alias=AliasChoices(
            "client_request_id",
            "clientRequestId",
            "idempotency_key",
            "idempotencyKey",
        ),
        serialization_alias="clientRequestId",
    )
    meal_occurred_at: str | None = Field(
        default=None,
        validation_alias=AliasChoices("meal_occurred_at", "mealOccurredAt"),
        serialization_alias="mealOccurredAt",
    )

    @field_validator("meal_description")
    @classmethod
    def validate_meal_description(cls, value: str) -> str:
        normalized = " ".join(value.strip().split())
        if normalized:
            return normalized
        raise ValueError("meal_description cannot be empty")

    @field_validator("client_request_id")
    @classmethod
    def validate_client_request_id(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("client_request_id cannot be empty")
        if len(normalized) > 128:
            raise ValueError("client_request_id cannot exceed 128 characters")
        return normalized

    @field_validator("meal_occurred_at")
    @classmethod
    def validate_from_estimate_meal_occurred_at(cls, value: str | None) -> str | None:
        return _normalize_timestamp_string(value)


class FoodLogFromEstimateResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    client_request_id: str = Field(
        validation_alias=AliasChoices("client_request_id", "clientRequestId"),
        serialization_alias="clientRequestId",
    )
    food_log_id: str = Field(
        validation_alias=AliasChoices("food_log_id", "foodLogId"),
        serialization_alias="foodLogId",
    )
    save_status: Literal["saved"] = Field(
        default="saved",
        validation_alias=AliasChoices("save_status", "saveStatus"),
        serialization_alias="saveStatus",
    )
    food_log: FoodLogEntryOut = Field(
        validation_alias=AliasChoices("food_log", "foodLog"),
        serialization_alias="foodLog",
    )


def serialize_food_log_entry(entry: dict[str, object]) -> FoodLogEntryOut:
    saved_at = _resolve_saved_at_value(entry)
    meal_occurred_at = _resolve_meal_occurred_at_value(entry, saved_at)
    timestamp = _parse_timestamp(meal_occurred_at)
    breakdown = parse_food_log_items(entry["ingredients_json"])
    protein, carbs, fat = _sum_macros_from_items(breakdown)
    decision_card = _deserialize_food_log_decision_card(entry.get("decision_card_json"))
    category, brand_group = _resolve_food_log_hierarchy(
        entry,
        decision_card=decision_card,
    )

    return FoodLogEntryOut.model_validate(
        {
            "id": str(entry["id"]),
            "name": entry["result_title"],
            "description": entry["result_description"],
            "calories": _normalize_calories(entry["total_calories"]),
            "date": _format_entry_date(timestamp),
            "time": _format_entry_time(timestamp),
            "breakdown": breakdown,
            "image": entry.get("display_image"),
            "image_source": entry.get("display_image_source"),
            "image_license": entry.get("display_image_license"),
            "standard_dish_id": (
                str(entry["standard_dish_id"])
                if entry.get("standard_dish_id") is not None
                else None
            ),
            "standard_dish_name": entry.get("standard_dish_name"),
            "protein": protein,
            "carbs": carbs,
            "fat": fat,
            "saved_at": saved_at,
            "meal_occurred_at": meal_occurred_at,
            "status": entry["status"],
            "source_type": entry["source_type"],
            "is_manual": bool(entry["is_manual"]),
            "idempotency_key": entry.get("idempotency_key"),
            "session_id": (
                str(entry["session_id"])
                if entry.get("session_id") is not None
                else None
            ),
            "source_message_id": (
                str(entry["source_message_id"])
                if entry.get("source_message_id") is not None
                else None
            ),
            "decision_card": decision_card,
            "category": category,
            "brand_group": brand_group,
        }
    )


def serialize_food_log_from_estimate_response(
    entry: dict[str, object],
    *,
    client_request_id: str,
) -> FoodLogFromEstimateResponse:
    food_log = serialize_food_log_entry(entry)
    return FoodLogFromEstimateResponse(
        client_request_id=client_request_id,
        food_log_id=food_log.id,
        save_status="saved",
        food_log=food_log,
    )


def _deserialize_food_log_decision_card(value: object) -> dict[str, object] | None:
    if not isinstance(value, str) or not value.strip():
        return None

    try:
        payload = json.loads(value)
        decision_card = DecisionCard.model_validate(payload)
    except (json.JSONDecodeError, TypeError, ValueError):
        return None

    return decision_card.model_dump(by_alias=True)


def _resolve_food_log_hierarchy(
    entry: dict[str, object],
    *,
    decision_card: dict[str, object] | None,
) -> tuple[dict[str, object], dict[str, object]]:
    normalized_product = _extract_normalized_product(decision_card)
    category = _resolve_primary_category(entry, normalized_product=normalized_product)
    brand_group = _resolve_brand_group(
        entry,
        normalized_product=normalized_product,
        primary_category=category,
    )
    return category, brand_group


def _extract_normalized_product(
    decision_card: dict[str, object] | None,
) -> dict[str, object]:
    if not isinstance(decision_card, dict):
        return {}

    normalized_product = decision_card.get("normalizedProduct")
    if not isinstance(normalized_product, dict):
        normalized_product = decision_card.get("normalized_product")
    return normalized_product if isinstance(normalized_product, dict) else {}


def _resolve_primary_category(
    entry: dict[str, object],
    *,
    normalized_product: dict[str, object],
) -> dict[str, object]:
    normalized_category_name = _normalize_optional_text(
        normalized_product.get("categoryName") or normalized_product.get("category_name")
    )
    if normalized_category_name:
        for definition in PRIMARY_CATEGORY_DEFINITIONS:
            if normalized_category_name in definition["category_names"]:
                return _build_primary_category_payload(definition)

    combined_text = _build_food_log_hierarchy_text(entry, normalized_product=normalized_product)
    combined_text_lower = combined_text.casefold()
    for definition in PRIMARY_CATEGORY_DEFINITIONS:
        if any(keyword.casefold() in combined_text_lower for keyword in definition["keywords"]):
            return _build_primary_category_payload(definition)

    return _build_primary_category_payload(DEFAULT_PRIMARY_CATEGORY)


def _build_primary_category_payload(
    definition: dict[str, object],
) -> dict[str, object]:
    return {
        "id": str(definition["id"]),
        "name": str(definition["name"]),
        "sort_order": int(definition["sort_order"]),
    }


def _resolve_brand_group(
    entry: dict[str, object],
    *,
    normalized_product: dict[str, object],
    primary_category: dict[str, object],
) -> dict[str, object]:
    brand_name = _normalize_optional_text(
        normalized_product.get("brandName") or normalized_product.get("brand_name")
    )
    brand_id = _normalize_optional_text(
        normalized_product.get("brandId") or normalized_product.get("brand_id")
    )
    if brand_name:
        resolved_brand_id = brand_id or f"brand:{_slugify_hierarchy_token(brand_name)}"
        return {
            "id": resolved_brand_id,
            "name": brand_name,
            "type": "brand",
            "sort_order": 10,
        }

    combined_text = _build_food_log_hierarchy_text(entry, normalized_product=normalized_product)
    combined_text_lower = combined_text.casefold()
    if any(marker in combined_text_lower for marker in HOMEMADE_MARKERS):
        return {
            "id": "homemade",
            "name": "自制餐食",
            "type": "homemade",
            "sort_order": 905,
        }

    if entry.get("source_type") == "manual":
        return {
            "id": "small_shop",
            "name": "小店菜品",
            "type": "small_shop",
            "sort_order": 910,
        }

    if primary_category["id"] == DEFAULT_PRIMARY_CATEGORY["id"]:
        return {
            "id": "unknown_source",
            "name": "来源未明确",
            "type": "unknown_source",
            "sort_order": 930,
        }

    return {
        "id": "no_brand",
        "name": "无品牌",
        "type": "no_brand",
        "sort_order": 920,
    }


def _build_food_log_hierarchy_text(
    entry: dict[str, object],
    *,
    normalized_product: dict[str, object],
) -> str:
    parts = [
        _normalize_optional_text(entry.get("meal_description")),
        _normalize_optional_text(entry.get("result_title")),
        _normalize_optional_text(entry.get("standard_dish_name")),
        _normalize_optional_text(
            normalized_product.get("productName") or normalized_product.get("product_name")
        ),
        _normalize_optional_text(
            normalized_product.get("normalizedName") or normalized_product.get("normalized_name")
        ),
    ]
    return " ".join(part for part in parts if part)


def _normalize_optional_text(value: object) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


def _slugify_hierarchy_token(value: str) -> str:
    normalized = value.strip().casefold()
    normalized = re.sub(r"\s+", "_", normalized)
    normalized = re.sub(r"[^\w\u4e00-\u9fff-]+", "", normalized)
    if normalized:
        return normalized
    return sha1(value.encode("utf-8")).hexdigest()[:12]


def parse_food_log_items(value: object) -> list[EstimateItem]:
    if not isinstance(value, str):
        raise ValueError("ingredients_json must be a JSON string")

    parsed = json.loads(value)
    if not isinstance(parsed, list):
        raise ValueError("ingredients_json must decode to a list")
    return [EstimateItem.model_validate(item) for item in parsed]


def _resolve_saved_at_value(entry: dict[str, object]) -> str:
    candidates = (
        entry.get("updated_at"),
        entry.get("created_at"),
        entry.get("logged_at"),
    )
    for value in candidates:
        if isinstance(value, str) and value.strip():
            return value
    return "1970-01-01 00:00:00"


def _resolve_meal_occurred_at_value(entry: dict[str, object], fallback: str) -> str:
    value = entry.get("meal_occurred_at")
    if isinstance(value, str) and value.strip():
        return value
    return fallback


def _parse_timestamp(value: str) -> datetime:
    try:
        return datetime.strptime(value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            return datetime.fromisoformat(value.replace("Z", "+00:00"))
        except ValueError:
            return datetime(1970, 1, 1, 0, 0, 0)


def _format_entry_date(timestamp: datetime) -> str:
    return f"{MONTH_ABBREVIATIONS[timestamp.month - 1]} {timestamp.day}"


def _format_entry_time(timestamp: datetime) -> str:
    period = "AM" if timestamp.hour < 12 else "PM"
    hour = timestamp.hour % 12 or 12
    return f"{hour:02d}:{timestamp.minute:02d} {period}"


def _normalize_calories(value: object) -> str:
    if not isinstance(value, str):
        return "0"

    match = re.search(r"\d+(?:\.\d+)?", value.replace(",", ""))
    if match is None:
        return "0"
    return match.group(0)


def _extract_grams(value: str | None) -> float:
    if not value:
        return 0.0
    match = re.search(r"(\d+(?:\.\d+)?)", str(value).replace(",", ""))
    if match is None:
        return 0.0
    parsed = float(match.group(1))
    return parsed if parsed == parsed else 0.0  # NaN guard


def _format_grams(total: float) -> str | None:
    if total <= 0:
        return None
    return f"{total:.1f} g" if total != int(total) else f"{int(total)} g"


def _sum_macros_from_items(
    items: list[EstimateItem],
) -> tuple[str | None, str | None, str | None]:
    total_protein = sum(_extract_grams(item.protein) for item in items)
    total_carbs = sum(_extract_grams(item.carbs) for item in items)
    total_fat = sum(_extract_grams(item.fat) for item in items)
    return (
        _format_grams(total_protein),
        _format_grams(total_carbs),
        _format_grams(total_fat),
    )


def _normalize_timestamp_string(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    if not normalized:
        return None
    normalized_value = normalized.replace("T", " ")
    try:
        timestamp = datetime.strptime(normalized_value, "%Y-%m-%d %H:%M:%S")
    except ValueError:
        try:
            timestamp = datetime.fromisoformat(normalized.replace("Z", "+00:00"))
        except ValueError as exc:
            raise ValueError(
                "meal_occurred_at must be ISO datetime or YYYY-MM-DD HH:MM:SS"
            ) from exc
    return timestamp.strftime("%Y-%m-%d %H:%M:%S")
