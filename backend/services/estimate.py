import json
import os
from pathlib import Path
from typing import Any
from urllib import error, parse, request

from backend.schemas.estimate import EstimateItem, EstimateResult


SYSTEM_INSTRUCTION = """
You are Food Pilot, a friendly and professional nutrition assistant.
Reply in Simplified Chinese.
Estimate calories conservatively, break down the meal into ingredients,
and provide a short practical suggestion.
Return only JSON that matches the requested schema.
""".strip()

RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "description": {"type": "STRING"},
        "confidence": {"type": "STRING"},
        "items": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "portion": {"type": "STRING"},
                    "energy": {"type": "STRING"},
                },
                "required": ["name", "portion", "energy"],
            },
        },
        "totalCalories": {"type": "STRING"},
        "suggestion": {"type": "STRING"},
    },
    "required": [
        "title",
        "description",
        "confidence",
        "items",
        "totalCalories",
        "suggestion",
    ],
}


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
    api_key = _get_api_key()
    if not api_key:
        raise ProviderUnavailableError("AI provider is not configured. Set GEMINI_API_KEY.", retryable=False)

    model_name = os.getenv("GEMINI_MODEL", "gemini-3-flash-preview")
    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{model_name}:generateContent?key={parse.quote(api_key)}"
    )

    payload = {
        "system_instruction": {
            "parts": [{"text": SYSTEM_INSTRUCTION}],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": query}],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA,
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
        with request.urlopen(req, timeout=20) as response:
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


def _get_api_key() -> str:
    env_key = os.getenv("GEMINI_API_KEY") or os.getenv("API_KEY")
    if env_key:
        return env_key

    project_root = Path(__file__).resolve().parents[2]
    candidate_files = [
        project_root / ".env",
        project_root / ".env.local",
        project_root / "frontend" / ".env.local",
    ]

    for env_file in candidate_files:
        loaded = _read_env_file(env_file, "GEMINI_API_KEY") or _read_env_file(env_file, "API_KEY")
        if loaded:
            return loaded

    return ""


def _read_env_file(path: Path, key: str) -> str:
    if not path.exists():
        return ""

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        current_key, current_value = line.split("=", 1)
        if current_key.strip() != key:
            continue

        return current_value.strip().strip("'\"")

    return ""
