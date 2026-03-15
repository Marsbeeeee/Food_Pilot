from typing import Any

from pydantic import ValidationError

from backend.schemas.estimate import EstimateResult


DEFAULT_TITLE = "餐食营养估算"
DEFAULT_DESCRIPTION = "这是根据你的描述给出的热量和营养大致拆解。"
DEFAULT_CONFIDENCE = "中"
DEFAULT_SUGGESTION = "如果补充份量、做法或食材细节，估算会更准确。"
DEFAULT_PORTION = "未说明"


def parse_estimate_payload(payload: dict[str, Any]) -> EstimateResult:
    normalized_payload = {
        "title": _coerce_text(
            payload.get("title")
            or payload.get("meal_title")
            or payload.get("mealTitle")
        ) or DEFAULT_TITLE,
        "description": _coerce_text(
            payload.get("description")
            or payload.get("summary")
        ) or DEFAULT_DESCRIPTION,
        "confidence": _coerce_text(
            payload.get("confidence")
            or payload.get("certainty")
        ) or DEFAULT_CONFIDENCE,
        "items": _normalize_items(payload.get("items")),
        "total_calories": _coerce_text(
            payload.get("total_calories")
            or payload.get("totalCalories")
            or payload.get("total")
            or payload.get("total_energy")
            or payload.get("totalEnergy")
            or payload.get("total_kcal")
            or payload.get("totalKcal")
        ),
        "suggestion": _coerce_text(
            payload.get("suggestion")
            or payload.get("advice")
            or payload.get("tip")
        ) or DEFAULT_SUGGESTION,
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

        name = _coerce_text(
            raw_item.get("name")
            or raw_item.get("ingredient")
            or raw_item.get("title")
        )
        portion = _coerce_text(
            raw_item.get("portion")
            or raw_item.get("amount")
            or raw_item.get("serving")
        )
        energy = _coerce_text(
            raw_item.get("energy")
            or raw_item.get("calories")
            or raw_item.get("kcal")
        )

        if not name or not energy:
            continue

        normalized_items.append(
            {
                "name": name,
                "portion": portion or DEFAULT_PORTION,
                "energy": energy,
            }
        )

    return normalized_items


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
