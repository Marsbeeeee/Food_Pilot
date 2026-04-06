"""Temporary analysis-eligibility policy for decision cards.

This sits in front of the future product-understanding layer so we can flip
the contract direction now without over-connecting Food Log / Insights flows.
"""

from __future__ import annotations


BRANDED_ANALYSIS_ALLOWLIST = (
    "霸王茶姬",
    "喜茶",
    "奈雪",
    "瑞幸",
    "库迪",
    "cotti",
    "luckin",
)

SOURCE_AMBIGUOUS_MARKERS = (
    "自制",
    "自家",
    "home made",
    "homemade",
)

GENERIC_LIGHT_MEAL_TERMS = (
    "沙拉",
    "salad",
)


def resolve_analysis_eligibility(
    *,
    input_summary: str,
    title: str,
    has_nutrition_estimate: bool,
    needs_clarification: bool,
    normalized_product: dict[str, object] | None = None,
) -> bool:
    if not has_nutrition_estimate or needs_clarification:
        return False

    if normalized_product:
        match_level = str(normalized_product.get("match_level") or normalized_product.get("matchLevel") or "").strip().casefold()
        missing_fields = normalized_product.get("missing_fields") or normalized_product.get("missingFields") or []
        if match_level in {"brand_only", "unknown"}:
            return False
        if match_level == "source_ambiguous":
            return False
        if isinstance(missing_fields, list) and any(str(field).strip() for field in missing_fields):
            return False

    normalized = f"{input_summary} {title}".strip().casefold()
    if not normalized:
        return False

    if _contains_any(normalized, BRANDED_ANALYSIS_ALLOWLIST):
        return True

    if _contains_any(normalized, SOURCE_AMBIGUOUS_MARKERS):
        return False

    # Temporary rule: generic light-meal labels are still too source-ambiguous
    # for analysis until the product-understanding layer lands.
    if _contains_any(normalized, GENERIC_LIGHT_MEAL_TERMS):
        return False

    return True


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term.casefold() in text for term in terms)
