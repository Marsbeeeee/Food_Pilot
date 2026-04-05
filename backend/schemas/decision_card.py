from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field
from backend.services.analysis_eligibility import resolve_analysis_eligibility


DecisionConfidenceLevel = Literal["high", "medium", "low", "unknown"]


class DecisionCardNormalizedProduct(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    category_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("category_id", "categoryId"),
        serialization_alias="categoryId",
    )
    category_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("category_name", "categoryName"),
        serialization_alias="categoryName",
    )
    brand_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("brand_id", "brandId"),
        serialization_alias="brandId",
    )
    brand_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("brand_name", "brandName"),
        serialization_alias="brandName",
    )
    product_id: str | None = Field(
        default=None,
        validation_alias=AliasChoices("product_id", "productId"),
        serialization_alias="productId",
    )
    product_name: str = Field(
        validation_alias=AliasChoices("product_name", "productName"),
        serialization_alias="productName",
    )
    product_scope: str = Field(
        default="single_item",
        validation_alias=AliasChoices("product_scope", "productScope"),
        serialization_alias="productScope",
    )
    item_role: str = Field(
        default="top_level_item",
        validation_alias=AliasChoices("item_role", "itemRole"),
        serialization_alias="itemRole",
    )


class DecisionCardNutritionEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    items: list[dict[str, Any]]
    total_calories: str = Field(
        validation_alias=AliasChoices("total_calories", "totalCalories"),
        serialization_alias="totalCalories",
    )


class DecisionCard(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    input_summary: str = Field(
        validation_alias=AliasChoices("input_summary", "inputSummary"),
        serialization_alias="inputSummary",
    )
    normalized_product: DecisionCardNormalizedProduct = Field(
        validation_alias=AliasChoices("normalized_product", "normalizedProduct"),
        serialization_alias="normalizedProduct",
    )
    nutrition_estimate: DecisionCardNutritionEstimate = Field(
        validation_alias=AliasChoices("nutrition_estimate", "nutritionEstimate"),
        serialization_alias="nutritionEstimate",
    )
    confidence_level: DecisionConfidenceLevel = Field(
        default="unknown",
        validation_alias=AliasChoices("confidence_level", "confidenceLevel"),
        serialization_alias="confidenceLevel",
    )
    recommendation_level: str = Field(
        default="needs_review",
        validation_alias=AliasChoices("recommendation_level", "recommendationLevel"),
        serialization_alias="recommendationLevel",
    )
    risk_tags: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("risk_tags", "riskTags"),
        serialization_alias="riskTags",
    )
    adaptation_note: str | None = Field(
        default=None,
        validation_alias=AliasChoices("adaptation_note", "adaptationNote"),
        serialization_alias="adaptationNote",
    )
    adjustments: list[str] = Field(default_factory=list)
    alternatives: list[str] = Field(default_factory=list)
    needs_clarification: bool = Field(
        default=False,
        validation_alias=AliasChoices("needs_clarification", "needsClarification"),
        serialization_alias="needsClarification",
    )
    save_container_key: str = Field(
        validation_alias=AliasChoices("save_container_key", "saveContainerKey"),
        serialization_alias="saveContainerKey",
    )
    container_type: str = Field(
        validation_alias=AliasChoices("container_type", "containerType"),
        serialization_alias="containerType",
    )
    analysis_eligible: bool = Field(
        default=False,
        validation_alias=AliasChoices("analysis_eligible", "analysisEligible"),
        serialization_alias="analysisEligible",
    )
    save_eligible: bool = Field(
        default=True,
        validation_alias=AliasChoices("save_eligible", "saveEligible"),
        serialization_alias="saveEligible",
    )


def normalize_confidence_level(value: str | None) -> DecisionConfidenceLevel:
    if value is None:
        return "unknown"

    normalized = value.strip().lower()
    if not normalized:
        return "unknown"

    if normalized in {"高", "较高", "high"}:
        return "high"
    if normalized in {"中", "中等", "适中", "medium", "mid"}:
        return "medium"
    if normalized in {"低", "较低", "high risk", "low"}:
        return "low"
    return "unknown"


def build_decision_card_from_estimate(
    *,
    input_summary: str,
    title: str,
    confidence: str | None,
    description: str | None,
    items: list[Any] | None,
    total_calories: str | None,
    suggestion: str | None,
    container_type: str,
    save_container_key: str | None = None,
    needs_clarification: bool | None = None,
    analysis_eligible: bool | None = None,
) -> DecisionCard:
    normalized_input = _normalize_text(input_summary) or _normalize_text(title) or "未命名输入"
    normalized_title = _normalize_text(title) or normalized_input
    normalized_items = _normalize_items(items)
    normalized_total = _normalize_text(total_calories) or "未提供"
    confidence_level = normalize_confidence_level(confidence)
    has_nutrition_estimate = bool(normalized_items) and normalized_total != "未提供"

    if needs_clarification is None:
        needs_clarification = (
            confidence_level in {"low", "unknown"}
            or not has_nutrition_estimate
        )

    if analysis_eligible is None:
        analysis_eligible = resolve_analysis_eligibility(
            input_summary=normalized_input,
            title=normalized_title,
            has_nutrition_estimate=has_nutrition_estimate,
            needs_clarification=needs_clarification,
        )

    recommendation_level = _recommendation_level_from_confidence(
        confidence_level,
        needs_clarification=needs_clarification,
    )
    risk_tags = []
    if needs_clarification:
        risk_tags.append("needs_clarification")
    if confidence_level == "low":
        risk_tags.append("low_confidence")

    if save_container_key is None:
        save_container_key = _build_save_container_key(
            container_type=container_type,
            input_summary=normalized_input,
            title=normalized_title,
            total_calories=normalized_total,
        )

    product_scope = "multi_item" if len(normalized_items) > 1 else "single_item"
    item_role = "top_level_item" if product_scope == "multi_item" else "single_item"
    adaptation_note = _normalize_text(description) or None
    adjustments = [_normalize_text(suggestion)] if _normalize_text(suggestion) else []

    return DecisionCard.model_validate(
        {
            "input_summary": normalized_input,
            "normalized_product": {
                "product_name": normalized_title,
                "product_scope": product_scope,
                "item_role": item_role,
            },
            "nutrition_estimate": {
                "items": normalized_items,
                "total_calories": normalized_total,
            },
            "confidence_level": confidence_level,
            "recommendation_level": recommendation_level,
            "risk_tags": risk_tags,
            "adaptation_note": adaptation_note,
            "adjustments": adjustments,
            "alternatives": [],
            "needs_clarification": needs_clarification,
            "save_container_key": save_container_key,
            "container_type": container_type,
            "analysis_eligible": analysis_eligible,
            "save_eligible": has_nutrition_estimate,
        }
    )


def build_clarification_decision_card(
    *,
    input_summary: str,
    container_type: str,
    reason: str | None = None,
) -> DecisionCard:
    normalized_input = _normalize_text(input_summary) or "未命名输入"
    save_container_key = _build_save_container_key(
        container_type=container_type,
        input_summary=normalized_input,
        title="clarification",
        total_calories="none",
    )
    risk_tags = ["needs_clarification"]
    if reason:
        risk_tags.append(_normalize_tag(reason))

    return DecisionCard.model_validate(
        {
            "input_summary": normalized_input,
            "normalized_product": {
                "product_name": normalized_input,
                "product_scope": "unknown",
                "item_role": "unknown",
            },
            "nutrition_estimate": {
                "items": [],
                "total_calories": "未提供",
            },
            "confidence_level": "low",
            "recommendation_level": "needs_review",
            "risk_tags": risk_tags,
            "adaptation_note": "当前信息不足，需要进一步澄清后再给出稳定决策。",
            "adjustments": [],
            "alternatives": [],
            "needs_clarification": True,
            "save_container_key": save_container_key,
            "container_type": container_type,
            "analysis_eligible": False,
            "save_eligible": False,
        }
    )


def _normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _normalize_items(items: list[Any] | None) -> list[dict[str, Any]]:
    if not items:
        return []

    normalized: list[dict[str, Any]] = []
    for item in items:
        if hasattr(item, "model_dump"):
            normalized_item = item.model_dump()
        elif isinstance(item, dict):
            normalized_item = dict(item)
        else:
            continue

        if not isinstance(normalized_item, dict):
            continue
        normalized.append(normalized_item)
    return normalized


def _recommendation_level_from_confidence(
    confidence_level: DecisionConfidenceLevel,
    *,
    needs_clarification: bool,
) -> str:
    if needs_clarification:
        return "needs_review"
    if confidence_level == "high":
        return "recommended"
    if confidence_level == "medium":
        return "acceptable"
    return "needs_review"


def _build_save_container_key(
    *,
    container_type: str,
    input_summary: str,
    title: str,
    total_calories: str,
) -> str:
    seed_payload = {
        "containerType": container_type,
        "inputSummary": input_summary,
        "title": title,
        "totalCalories": total_calories,
    }
    digest = hashlib.sha1(
        json.dumps(seed_payload, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    return f"{container_type}:{digest}"


def _normalize_tag(value: str) -> str:
    return value.strip().lower().replace(" ", "_")
