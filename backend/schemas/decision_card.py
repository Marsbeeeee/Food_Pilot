from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field

from backend.schemas.profile import ProfileOut
from backend.services.analysis_eligibility import resolve_analysis_eligibility
from backend.services.brand_estimation import resolve_brand_estimation
from backend.services.personalized_decision import resolve_personalized_decision
from backend.services.product_understanding import build_product_understanding


DecisionConfidenceLevel = Literal["high", "medium", "low", "unknown"]
_MISSING_TOTAL = "未提供"
_UNKNOWN_INPUT = "未命名输入"


class DecisionCardProductComponent(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    product_name: str = Field(
        validation_alias=AliasChoices("product_name", "productName"),
        serialization_alias="productName",
    )
    normalized_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("normalized_name", "normalizedName"),
        serialization_alias="normalizedName",
    )
    category_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("category_name", "categoryName"),
        serialization_alias="categoryName",
    )
    brand_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("brand_name", "brandName"),
        serialization_alias="brandName",
    )
    item_role: str = Field(
        default="component",
        validation_alias=AliasChoices("item_role", "itemRole"),
        serialization_alias="itemRole",
    )
    quantity: str | None = None


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
    normalized_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("normalized_name", "normalizedName"),
        serialization_alias="normalizedName",
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
    size_or_spec: str | None = Field(
        default=None,
        validation_alias=AliasChoices("size_or_spec", "sizeOrSpec"),
        serialization_alias="sizeOrSpec",
    )
    addons: list[str] = Field(default_factory=list)
    sugar_level: str | None = Field(
        default=None,
        validation_alias=AliasChoices("sugar_level", "sugarLevel"),
        serialization_alias="sugarLevel",
    )
    milk_base: str | None = Field(
        default=None,
        validation_alias=AliasChoices("milk_base", "milkBase"),
        serialization_alias="milkBase",
    )
    temperature: str | None = None
    quantity: str | None = None
    combo_items: list[DecisionCardProductComponent] = Field(
        default_factory=list,
        validation_alias=AliasChoices("combo_items", "comboItems"),
        serialization_alias="comboItems",
    )
    missing_fields: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("missing_fields", "missingFields"),
        serialization_alias="missingFields",
    )
    match_level: str = Field(
        default="unknown",
        validation_alias=AliasChoices("match_level", "matchLevel"),
        serialization_alias="matchLevel",
    )


class DecisionCardNutritionEstimate(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    items: list[dict[str, Any]]
    total_calories: str = Field(
        validation_alias=AliasChoices("total_calories", "totalCalories"),
        serialization_alias="totalCalories",
    )


class DecisionCardEstimationMeta(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    source_type: str = Field(
        validation_alias=AliasChoices("source_type", "sourceType"),
        serialization_alias="sourceType",
    )
    source_label: str = Field(
        validation_alias=AliasChoices("source_label", "sourceLabel"),
        serialization_alias="sourceLabel",
    )
    template_id: str = Field(
        validation_alias=AliasChoices("template_id", "templateId"),
        serialization_alias="templateId",
    )
    hit_level: str = Field(
        validation_alias=AliasChoices("hit_level", "hitLevel"),
        serialization_alias="hitLevel",
    )
    fallback_path: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("fallback_path", "fallbackPath"),
        serialization_alias="fallbackPath",
    )
    confidence_reasons: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("confidence_reasons", "confidenceReasons"),
        serialization_alias="confidenceReasons",
    )
    applied_rules: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("applied_rules", "appliedRules"),
        serialization_alias="appliedRules",
    )
    missing_configuration: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("missing_configuration", "missingConfiguration"),
        serialization_alias="missingConfiguration",
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
    estimation_meta: DecisionCardEstimationMeta | None = Field(
        default=None,
        validation_alias=AliasChoices("estimation_meta", "estimationMeta"),
        serialization_alias="estimationMeta",
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
    is_personalized: bool = Field(
        default=False,
        validation_alias=AliasChoices("is_personalized", "isPersonalized"),
        serialization_alias="isPersonalized",
    )
    personalization_note: str | None = Field(
        default=None,
        validation_alias=AliasChoices("personalization_note", "personalizationNote"),
        serialization_alias="personalizationNote",
    )
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
    profile: ProfileOut | None = None,
    profile_requested: bool = False,
) -> DecisionCard:
    normalized_input = _normalize_text(input_summary) or _normalize_text(title) or _UNKNOWN_INPUT
    normalized_title = _normalize_text(title) or normalized_input
    normalized_items = _normalize_items(items)
    normalized_total = _normalize_text(total_calories) or _MISSING_TOTAL
    product_understanding = build_product_understanding(
        input_summary=normalized_input,
        title=normalized_title,
        items=normalized_items,
    )
    estimation_snapshot = resolve_brand_estimation(
        input_summary=normalized_input,
        title=normalized_title,
        items=normalized_items,
        product_understanding=product_understanding,
    )
    confidence_level = _merge_confidence_levels(
        normalize_confidence_level(
            confidence if confidence is not None else _extract_estimation_confidence(estimation_snapshot)
        ),
        product_understanding["confidence_level"],
    )
    has_nutrition_estimate = bool(normalized_items) and normalized_total != _MISSING_TOTAL

    if needs_clarification is None:
        needs_clarification = (
            bool(product_understanding["needs_clarification"])
            or confidence_level in {"low", "unknown"}
            or not has_nutrition_estimate
        )

    if analysis_eligible is None:
        analysis_eligible = resolve_analysis_eligibility(
            input_summary=normalized_input,
            title=normalized_title,
            has_nutrition_estimate=has_nutrition_estimate,
            needs_clarification=needs_clarification,
            normalized_product=product_understanding["normalized_product"],
        )

    if save_container_key is None:
        save_container_key = _build_save_container_key(
            container_type=container_type,
            input_summary=normalized_input,
            title=normalized_title,
            total_calories=normalized_total,
        )

    risk_tags = list(product_understanding["risk_tags"])
    if needs_clarification:
        risk_tags.append("needs_clarification")
    if confidence_level == "low":
        risk_tags.append("low_confidence")

    personalized_decision = resolve_personalized_decision(
        input_summary=normalized_input,
        normalized_product=product_understanding["normalized_product"],
        nutrition_items=normalized_items,
        total_calories=normalized_total,
        confidence_level=confidence_level,
        description=description,
        suggestion=suggestion,
        profile=profile,
        profile_requested=profile_requested,
        needs_clarification=needs_clarification,
    )
    risk_tags.extend(personalized_decision.risk_tags)
    adaptation_note = (
        _normalize_text(personalized_decision.adaptation_note)
        or _normalize_text(description)
        or None
    )
    adjustments = personalized_decision.adjustments
    alternatives = personalized_decision.alternatives

    return DecisionCard.model_validate(
        {
            "input_summary": normalized_input,
            "normalized_product": product_understanding["normalized_product"],
            "nutrition_estimate": {
                "items": normalized_items,
                "total_calories": normalized_total,
            },
            "estimation_meta": (
                estimation_snapshot["estimation_meta"] if estimation_snapshot is not None else None
            ),
            "confidence_level": confidence_level,
            "recommendation_level": personalized_decision.recommendation_level,
            "risk_tags": _dedupe_tags(risk_tags),
            "adaptation_note": adaptation_note,
            "adjustments": adjustments,
            "alternatives": alternatives,
            "is_personalized": personalized_decision.is_personalized,
            "personalization_note": personalized_decision.personalization_note,
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
    normalized_input = _normalize_text(input_summary) or _UNKNOWN_INPUT
    product_understanding = build_product_understanding(
        input_summary=normalized_input,
        title=normalized_input,
        items=None,
        clarification_reason=reason,
    )
    save_container_key = _build_save_container_key(
        container_type=container_type,
        input_summary=normalized_input,
        title="clarification",
        total_calories="none",
    )

    return DecisionCard.model_validate(
        {
            "input_summary": normalized_input,
            "normalized_product": product_understanding["normalized_product"],
            "nutrition_estimate": {
                "items": [],
                "total_calories": _MISSING_TOTAL,
            },
            "confidence_level": "low",
            "recommendation_level": "needs_review",
            "risk_tags": _dedupe_tags(
                ["needs_clarification", *product_understanding["risk_tags"]]
            ),
            "adaptation_note": "当前信息还不足以形成稳定商品理解，请先补充关键商品信息。",
            "adjustments": product_understanding["clarification_questions"],
            "alternatives": [],
            "is_personalized": False,
            "personalization_note": "商品信息不足，暂未进入稳定的个体化判断。",
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


def _extract_estimation_confidence(estimation_snapshot: dict[str, Any] | None) -> str | None:
    if not estimation_snapshot:
        return None
    value = estimation_snapshot.get("confidence")
    return value if isinstance(value, str) else None


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


def _merge_confidence_levels(
    estimate_confidence: DecisionConfidenceLevel,
    understanding_confidence: str | None,
) -> DecisionConfidenceLevel:
    ranking = {"high": 3, "medium": 2, "low": 1, "unknown": 0}
    normalized_understanding = normalize_confidence_level(understanding_confidence)
    return (
        estimate_confidence
        if ranking[estimate_confidence] <= ranking[normalized_understanding]
        else normalized_understanding
    )


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


def _dedupe_tags(values: list[str]) -> list[str]:
    deduped: list[str] = []
    for value in values:
        normalized = _normalize_tag(value)
        if not normalized or normalized in deduped:
            continue
        deduped.append(normalized)
    return deduped
