import json
from typing import Any
from urllib import error, parse, request

from backend.config.estimate import get_estimate_ai_config
from backend.schemas.profile import ProfileOut
from backend.schemas.recommendation import GuidanceReply
from backend.services.profile_service import get_profile
from backend.services.recommendation_contract import (
    GUIDANCE_RESPONSE_INSTRUCTIONS,
    GUIDANCE_RESPONSE_SCHEMA,
)


DEFAULT_RECOMMENDATION_SYSTEM_PROMPT = """
You are Food Pilot, a friendly and practical nutrition assistant.
Reply in Simplified Chinese.
For recommendation requests, focus on actionable meal choices, comparisons, swaps, and optimization suggestions.
Always give the user a concrete choice or direction first, then explain briefly why it fits.
Do not turn recommendation requests into calorie-estimate tables or ingredient breakdowns.
For text requests, act only as an auxiliary fallback for small talk, explanatory follow-ups,
and short clarifications about an existing recommendation or estimate.
Do not expand text requests into a third complex capability, a new recommendation plan, or a fresh estimate.
Return only JSON that matches the requested schema.
""".strip()

DEFAULT_GUIDANCE_COPY = {
    "meal_recommendation": {
        "title": "餐食推荐",
        "description": "这是基于你当前问题给出的推荐建议。",
    },
    "text": {
        "title": "补充说明",
        "description": "这是对当前问题的补充说明。",
    },
}


class RecommendationServiceError(Exception):
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


class MissingAPIKeyError(RecommendationServiceError):
    def __init__(self) -> None:
        super().__init__(
            code="AI_CONFIG_MISSING",
            status_code=503,
            message="GEMINI_API_KEY is missing",
            user_message="推荐服务暂未配置，请稍后再试。",
            retryable=False,
        )


class UpstreamAIError(RecommendationServiceError):
    def __init__(self, message: str, *, retryable: bool) -> None:
        super().__init__(
            code="AI_UPSTREAM_ERROR",
            status_code=503,
            message=message,
            user_message="推荐服务暂时不可用，请稍后重试。",
            retryable=retryable,
        )


class InvalidAIResponseError(RecommendationServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(
            code="AI_RESPONSE_INVALID",
            status_code=502,
            message=message,
            user_message="推荐服务返回结果异常，请稍后重试。",
            retryable=True,
        )


class IncompleteAIResponseError(RecommendationServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(
            code="AI_RESPONSE_INCOMPLETE",
            status_code=502,
            message=message,
            user_message="推荐服务返回结果不完整，请稍后重试。",
            retryable=True,
        )


def generate_meal_recommendation(
    query: str,
    profile_id: int | None = None,
    user_id: int | None = None,
) -> GuidanceReply:
    return _generate_guidance(
        query,
        response_mode="meal_recommendation",
        profile_id=profile_id,
        user_id=user_id,
    )


def generate_text_reply(
    query: str,
    profile_id: int | None = None,
    user_id: int | None = None,
) -> GuidanceReply:
    return _generate_guidance(
        query,
        response_mode="text",
        profile_id=profile_id,
        user_id=user_id,
    )


def _generate_guidance(
    query: str,
    *,
    response_mode: str,
    profile_id: int | None,
    user_id: int | None,
) -> GuidanceReply:
    # 统一在入口尝试加载 Profile：如果有 profile_id，则始终加载 Profile 对象；
    # 若未设置或加载失败，则使用显式的占位（profile=None），但仍以一致的方式向下传递。
    _, profile_context = _load_profile_and_context(profile_id, user_id)
    raw_response = _call_gemini_api(query, response_mode=response_mode, profile_context=profile_context)
    try:
        return _parse_guidance_payload(raw_response, response_mode=response_mode)
    except ValueError as exc:
        if str(exc) == "AI response is missing response":
            raise IncompleteAIResponseError(str(exc)) from exc
        raise InvalidAIResponseError(str(exc)) from exc


def _call_gemini_api(
    query: str,
    *,
    response_mode: str,
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
                    "text": _build_guidance_system_instruction(
                        response_mode=response_mode,
                        profile_context=profile_context,
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
            "responseSchema": GUIDANCE_RESPONSE_SCHEMA,
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


def _load_profile_and_context(
    profile_id: int | None,
    user_id: int | None,
) -> tuple[ProfileOut | None, str | None]:
    if profile_id is None or user_id is None:
        return None, None

    profile = get_profile(profile_id, user_id)
    if profile is None:
        return None, None

    return profile, _build_profile_context(profile)


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


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
