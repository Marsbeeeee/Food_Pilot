import json
from typing import Any
from urllib import error, request

from backend.config.estimate import get_estimate_ai_config
from backend.services.ai_client import call_ai
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
    raw_response = _call_ai_api(query, response_mode=response_mode, profile_context=profile_context)
    try:
        return _parse_guidance_payload(raw_response, response_mode=response_mode)
    except ValueError as exc:
        if str(exc) == "AI response is missing response":
            raise IncompleteAIResponseError(str(exc)) from exc
        raise InvalidAIResponseError(str(exc)) from exc


def _call_ai_api(
    query: str,
    *,
    response_mode: str,
    profile_context: str | None = None,
) -> dict[str, Any]:
    config = get_estimate_ai_config()
    if not config.api_key:
        raise MissingAPIKeyError()

    system_prompt = _build_guidance_system_instruction(
        response_mode=response_mode,
        profile_context=profile_context,
    )
    try:
        return call_ai(
            config,
            system_prompt,
            query,
            response_schema=GUIDANCE_RESPONSE_SCHEMA,
        )
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
    except json.JSONDecodeError as exc:
        raise InvalidAIResponseError("AI provider did not return valid JSON") from exc


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
    # Explicitly surface core fields for recommendations and make missing data visible,
    # so the model does not silently assume defaults.
    goal = profile.goal or "Unknown goal – do not assume a specific fat loss or muscle gain target."
    if getattr(profile, "kcal_target", None):
        kcal_target = f"{profile.kcal_target} kcal"
    else:
        kcal_target = "Unknown daily calorie target – do not infer a precise number."

    diet_style = profile.diet_style or "Unknown diet style – avoid overfitting to any specific pattern."

    if profile.allergies:
        allergies = (
            "The following ingredients MUST NOT appear in recommended foods: "
            + ", ".join(profile.allergies)
        )
    else:
        allergies = (
            "No explicit allergies reported in profile – only avoid ingredients the user "
            "states in the current conversation."
        )

    activity_level = profile.activity_level or "Unspecified"
    exercise_type = profile.exercise_type or "Unspecified"
    pace = profile.pace or "Unspecified"

    return "\n".join(
        [
            "User profile (for personalization):",
            f"- Goal: {goal}",
            f"- Daily calorie target: {kcal_target}",
            f"- Diet style: {diet_style}",
            f"- Allergies / avoidances: {allergies}",
            f"- Activity level: {activity_level}",
            f"- Exercise type: {exercise_type}",
            f"- Pace: {pace}",
        ]
    )


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def check_allergen_violations(
    recommended_items: Any,
    allergens: list[str] | tuple[str, ...],
) -> tuple[bool, list[str]]:
    """
    Check whether recommended content contains any of the given allergen keywords.

    This is a pure helper and does not perform any I/O. It is intended to be
    used as a post-processing safety check on model outputs.
    """
    if not allergens:
        return True, []

    text_fragments: list[str] = []

    def _collect(value: Any) -> None:
        if value is None:
            return
        if isinstance(value, str):
            text_fragments.append(value)
            return
        if isinstance(value, (list, tuple, set)):
            for item in value:
                _collect(item)
            return
        if isinstance(value, dict):
            for v in value.values():
                _collect(v)
            return
        # Fallback: coerce other primitive types to string
        if isinstance(value, (int, float, bool)):
            text_fragments.append(str(value))

    _collect(recommended_items)

    haystack = " ".join(text_fragments).lower()
    violations: list[str] = []
    for allergen in allergens:
        if not allergen:
            continue
        if str(allergen).lower() in haystack:
            violations.append(str(allergen))

    ok = not violations
    return ok, violations
