from typing import Any

from pydantic import ValidationError

from backend.schemas.estimate import EstimateResult


DEFAULT_TITLE = "Meal Estimate"
DEFAULT_DESCRIPTION = "Here is the estimated calorie breakdown based on your description."
DEFAULT_CONFIDENCE = "Medium"
DEFAULT_SUGGESTION = "Add portions, cooking methods, or ingredients for a more accurate estimate."


def parse_estimate_payload(payload: dict[str, Any]) -> EstimateResult:
    normalized_payload = {
        "title": _coerce_text(payload.get("title")) or DEFAULT_TITLE,
        "description": _coerce_text(payload.get("description")) or DEFAULT_DESCRIPTION,
        "confidence": _coerce_text(payload.get("confidence")) or DEFAULT_CONFIDENCE,
        "items": _normalize_items(payload.get("items")),
        "total_calories": _coerce_text(
            payload.get("total_calories")
            or payload.get("totalCalories")
            or payload.get("total")
        ),
        "suggestion": _coerce_text(payload.get("suggestion")) or DEFAULT_SUGGESTION,
    }

    if not normalized_payload["items"]:
        raise ValueError("AI response is missing item details")
    if not normalized_payload["total_calories"]:
        raise ValueError("AI response is missing total_calories")

    try:
        return EstimateResult.model_validate(normalized_payload)
    except ValidationError as exc:
        raise ValueError("AI response failed schema validation") from exc


def _normalize_items(raw_items: Any) -> list[dict[str, str]]:
    if not isinstance(raw_items, list):
        return []

    normalized_items: list[dict[str, str]] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue

        normalized_items.append(
            {
                "name": _coerce_text(raw_item.get("name")),
                "portion": _coerce_text(raw_item.get("portion")),
                "energy": _coerce_text(raw_item.get("energy")),
            }
        )

    return normalized_items


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
