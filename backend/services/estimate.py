import json
from typing import Any
from urllib import error, request

from backend.config.estimate import get_estimate_ai_config
from backend.schemas.knowledge import KnowledgeReference
from backend.schemas.estimate import EstimateItem, EstimateResult
from backend.schemas.profile import ProfileOut
from backend.services.ai_client import call_ai
from backend.services.estimate_contract import (
    ESTIMATE_RESPONSE_INSTRUCTION,
    ESTIMATE_RESPONSE_SCHEMA,
)
from backend.services.food_knowledge import (
    build_single_dish_ingredient_breakdown,
    retrieve_food_knowledge,
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


def estimate_meal(
    query: str,
    profile_id: int | None = None,
    user_id: int | None = None,
) -> EstimateResult:
    retrieved_knowledge = retrieve_food_knowledge(query, scenario="estimate")
    profile_context = _load_profile_context(profile_id, user_id)
    raw_response = _call_ai_api(
        query,
        profile_context,
        food_knowledge_context=retrieved_knowledge.context_text if retrieved_knowledge.has_hits else None,
    )
    try:
        parsed = parse_estimate_payload(raw_response)
    except ValueError as exc:
        if str(exc) in {
            "AI response is missing item details",
            "AI response is missing total_calories",
        }:
            raise IncompleteAIResponseError(str(exc)) from exc
        raise InvalidAIResponseError(str(exc)) from exc

    if _needs_multi_food_retry(parsed, retrieved_knowledge.hit_count):
        retry_raw_response = _call_ai_api(
            query,
            profile_context,
            food_knowledge_context=retrieved_knowledge.context_text if retrieved_knowledge.has_hits else None,
            force_min_items=min(max(retrieved_knowledge.hit_count, 2), 3),
        )
        try:
            retry_parsed = parse_estimate_payload(retry_raw_response)
            if len(retry_parsed.items) > len(parsed.items):
                parsed = retry_parsed
        except ValueError:
            # Keep the first valid parse to avoid breaking the main estimate flow.
            pass

    dish_breakdown = _maybe_build_single_dish_breakdown(parsed, query)
    if dish_breakdown:
        parsed = parsed.model_copy(
            update={
                "items": [
                    EstimateItem.model_validate(item)
                    for item in dish_breakdown
                ],
                "itemization_mode": "single_dish_ingredients",
            }
        )

    if retrieved_knowledge.references:
        parsed = parsed.model_copy(
            update={
                "knowledge_refs": [
                    KnowledgeReference.model_validate(ref)
                    for ref in retrieved_knowledge.references
                ]
            }
        )
    return parsed


def _call_ai_api(
    query: str,
    profile_context: str | None = None,
    *,
    food_knowledge_context: str | None = None,
    force_min_items: int | None = None,
) -> dict[str, Any]:
    config = get_estimate_ai_config()
    if not config.api_key:
        raise MissingAPIKeyError()

    system_prompt = _build_estimate_system_instruction(
        config.system_prompt,
        profile_context,
        food_knowledge_context=food_knowledge_context,
        force_min_items=force_min_items,
    )
    try:
        return call_ai(
            config,
            system_prompt,
            query,
            response_schema=ESTIMATE_RESPONSE_SCHEMA,
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


def _load_profile_context(
    profile_id: int | None,
    user_id: int | None,
) -> str | None:
    if profile_id is None or user_id is None:
        return None

    profile = get_profile(profile_id, user_id)
    if profile is None:
        return None

    return _build_profile_context(profile)


def _build_estimate_system_instruction(
    system_prompt: str,
    profile_context: str | None = None,
    *,
    food_knowledge_context: str | None = None,
    force_min_items: int | None = None,
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

    if food_knowledge_context:
        parts.extend(
            [
                (
                    "You are given a retrieved Chinese food knowledge context. "
                    "Use it as factual prior for dish/ingredient nutrition and portion assumptions."
                ),
                food_knowledge_context,
            ]
        )
    if force_min_items and force_min_items > 1:
        parts.append(
            (
                "Important formatting rule for this request: the user likely mentioned multiple foods. "
                f"Return at least {force_min_items} distinct items in `items`, one major food per item. "
                "Do not merge multiple foods into a single item row."
            )
        )
    parts.append(ESTIMATE_RESPONSE_INSTRUCTION)
    return "\n\n".join(parts)


def _needs_multi_food_retry(result: EstimateResult, knowledge_hit_count: int) -> bool:
    if knowledge_hit_count < 2:
        return False
    return len(result.items) < 2


def _maybe_build_single_dish_breakdown(
    result: EstimateResult,
    query: str,
) -> list[dict[str, str]] | None:
    if len(result.items) != 1:
        return None
    primary_item = result.items[0]
    return build_single_dish_ingredient_breakdown(
        query,
        primary_item_name=primary_item.name,
        total_calories_text=result.total_calories,
        primary_portion_text=primary_item.portion,
    )


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
