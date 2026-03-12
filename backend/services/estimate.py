import json
from typing import Any
from urllib import error, parse, request

from backend.config.estimate import get_estimate_ai_config
from backend.schemas.estimate import EstimateItem, EstimateResult
from backend.services.estimate_contract import (
    ESTIMATE_RESPONSE_INSTRUCTION,
    ESTIMATE_RESPONSE_SCHEMA,
)


class EstimateServiceError(Exception):
    def __init__(
        self,
        *,
        code: str,
        status_code: int,
        message: str,
        retryable: bool,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.message = message
        self.retryable = retryable


class ProviderUnavailableError(EstimateServiceError):
    def __init__(self, message: str, *, retryable: bool) -> None:
        super().__init__(
            code="AI_PROVIDER_UNAVAILABLE",
            status_code=503,
            message=message,
            retryable=retryable,
        )


class InvalidAIResponseError(EstimateServiceError):
    def __init__(self, message: str = "AI returned an invalid response format") -> None:
        super().__init__(
            code="AI_RESPONSE_INVALID",
            status_code=502,
            message=message,
            retryable=True,
        )


def estimate_meal(query: str) -> EstimateResult:
    raw_response = _call_gemini_api(query)
    return _normalize_estimate(raw_response)


def _call_gemini_api(query: str) -> dict[str, Any]:
    config = get_estimate_ai_config()
    if not config.api_key:
        raise ProviderUnavailableError("AI provider is not configured. Set GEMINI_API_KEY.", retryable=False)

    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.model}:generateContent?key={parse.quote(config.api_key)}"
    )

    payload = {
        "system_instruction": {
            "parts": [
                {
                    "text": (
                        f"{config.system_prompt}\n\n"
                        f"{ESTIMATE_RESPONSE_INSTRUCTION}"
                    )
                }
            ],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": query}],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": ESTIMATE_RESPONSE_SCHEMA,
        },
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=config.timeout_seconds) as response:
            response_data = json.load(response)
    except error.HTTPError as exc:
        exc.read()
        if exc.code in {401, 403}:
            raise ProviderUnavailableError("AI provider authentication failed. Check GEMINI_API_KEY.", retryable=False) from exc
        raise ProviderUnavailableError(
            f"AI provider request failed ({exc.code}).",
            retryable=exc.code >= 500,
        ) from exc
    except error.URLError as exc:
        raise ProviderUnavailableError("AI provider is temporarily unavailable. Please try again later.", retryable=True) from exc

    try:
        text = response_data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise InvalidAIResponseError("AI provider did not return parseable content") from exc

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InvalidAIResponseError("AI provider did not return valid JSON") from exc

    if not isinstance(parsed, dict):
        raise InvalidAIResponseError("AI provider returned JSON that is not an object")
    return parsed


def _normalize_estimate(payload: dict[str, Any]) -> EstimateResult:
    items = _normalize_items(payload.get("items"))
    total_calories = _coerce_text(
        payload.get("totalCalories")
        or payload.get("total_calories")
        or payload.get("total")
    )

    if not items:
        raise InvalidAIResponseError("AI response is missing item details")
    if not total_calories:
        raise InvalidAIResponseError("AI response is missing totalCalories")

    title = _coerce_text(payload.get("title")) or "Meal Estimate"
    description = (
        _coerce_text(payload.get("description"))
        or "Here is the estimated calorie breakdown based on your description."
    )
    confidence = _coerce_text(payload.get("confidence")) or "Medium"
    suggestion = (
        _coerce_text(payload.get("suggestion"))
        or "Add portions, cooking methods, or ingredients for a more accurate estimate."
    )

    return EstimateResult(
        title=title,
        description=description,
        confidence=confidence,
        items=items,
        totalCalories=total_calories,
        suggestion=suggestion,
    )


def _normalize_items(raw_items: Any) -> list[EstimateItem]:
    if not isinstance(raw_items, list):
        return []

    normalized_items: list[EstimateItem] = []
    for raw_item in raw_items:
        if not isinstance(raw_item, dict):
            continue

        name = _coerce_text(raw_item.get("name"))
        portion = _coerce_text(raw_item.get("portion"))
        energy = _coerce_text(raw_item.get("energy"))
        if not name or not portion or not energy:
            continue

        normalized_items.append(
            EstimateItem(name=name, portion=portion, energy=energy)
        )

    return normalized_items


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
