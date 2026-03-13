import json
from typing import Any
from urllib import error, parse, request

from backend.config.estimate import get_estimate_ai_config
from backend.schemas.estimate import EstimateResult
from backend.schemas.profile import ProfileOut
from backend.services.estimate_contract import (
    ESTIMATE_RESPONSE_INSTRUCTION,
    ESTIMATE_RESPONSE_SCHEMA,
)
from backend.services.estimate_parser import parse_estimate_payload
from backend.services.profile_service import get_profile


class EstimateServiceError(Exception):
    def __init__(
        self,
        *,
        code: str,
        status_code: int,
        message: str,
        user_message: str,
        retryable: bool,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.message = message
        self.user_message = user_message
        self.retryable = retryable


class MissingAPIKeyError(EstimateServiceError):
    def __init__(self) -> None:
        super().__init__(
            code="AI_CONFIG_MISSING",
            status_code=503,
            message="GEMINI_API_KEY is missing",
            user_message="AI 估算服务暂未配置，请稍后再试。",
            retryable=False,
        )


class UpstreamAIError(EstimateServiceError):
    def __init__(self, message: str, *, retryable: bool) -> None:
        super().__init__(
            code="AI_UPSTREAM_ERROR",
            status_code=503,
            message=message,
            user_message="AI 服务暂时不可用，请稍后重试。",
            retryable=retryable,
        )


class InvalidAIResponseError(EstimateServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(
            code="AI_RESPONSE_INVALID",
            status_code=502,
            message=message,
            user_message="AI 返回结果异常，请稍后重试。",
            retryable=True,
        )


class IncompleteAIResponseError(EstimateServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(
            code="AI_RESPONSE_INCOMPLETE",
            status_code=502,
            message=message,
            user_message="AI 返回结果不完整，请稍后重试。",
            retryable=True,
        )


def estimate_meal(query: str, profile_id: int | None = None) -> EstimateResult:
    profile_context = _load_profile_context(profile_id)
    raw_response = _call_gemini_api(query, profile_context)
    try:
        return parse_estimate_payload(raw_response)
    except ValueError as exc:
        if str(exc) in {
            "AI response is missing item details",
            "AI response is missing total_calories",
        }:
            raise IncompleteAIResponseError(str(exc)) from exc
        raise InvalidAIResponseError(str(exc)) from exc


def _call_gemini_api(
    query: str,
    profile_context: str | None = None,
) -> dict[str, Any]:
    config = get_estimate_ai_config()
    if not config.api_key:
        raise MissingAPIKeyError()

    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.model}:generateContent?key={parse.quote(config.api_key)}"
    )

    payload = {
        "system_instruction": {
            "parts": [
                {
                    "text": _build_estimate_system_instruction(
                        config.system_prompt,
                        profile_context,
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
            raise UpstreamAIError("AI provider authentication failed.", retryable=False) from exc
        raise UpstreamAIError(
            f"AI provider request failed ({exc.code}).",
            retryable=exc.code >= 500,
        ) from exc
    except error.URLError as exc:
        raise UpstreamAIError("AI provider is temporarily unavailable.", retryable=True) from exc

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


def _load_profile_context(profile_id: int | None) -> str | None:
    if profile_id is None:
        return None

    profile = get_profile(profile_id)
    if profile is None:
        return None

    return _build_profile_context(profile)


def _build_estimate_system_instruction(
    system_prompt: str,
    profile_context: str | None = None,
) -> str:
    parts = [system_prompt.strip()]

    if profile_context:
        parts.extend(
            [
                "Use the following user profile context when personalizing assumptions and the final suggestion.",
                profile_context,
                (
                    "When profile context is available, keep the calorie estimate grounded in the described meal, "
                    "but make the suggestion align with the user's goal, calorie target, diet style, and allergies."
                ),
                "Do not recommend foods that conflict with listed allergies or avoidances.",
            ]
        )

    parts.append(ESTIMATE_RESPONSE_INSTRUCTION)
    return "\n\n".join(parts)


def _build_profile_context(profile: ProfileOut) -> str:
    allergies = ", ".join(profile.allergies) if profile.allergies else "None reported"

    return "\n".join(
        [
            "User profile:",
            f"- Goal: {profile.goal}",
            f"- Daily calorie target: {profile.kcal_target} kcal",
            f"- Diet style: {profile.diet_style}",
            f"- Allergies / avoidances: {allergies}",
            f"- Activity level: {profile.activity_level}",
            f"- Exercise type: {profile.exercise_type}",
            f"- Pace: {profile.pace}",
        ]
    )
