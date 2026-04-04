import json
import re
from typing import Any
from urllib import error

from backend.config.estimate import get_estimate_ai_config
from backend.schemas.estimate import EstimateItem, EstimateResult
from backend.schemas.knowledge import KnowledgeReference
from backend.schemas.profile import ProfileOut
from backend.services.ai_client import call_ai
from backend.services.estimate_contract import (
    ESTIMATE_CAPABILITY_RULES,
    ESTIMATE_OUTPUT_CONTRACT,
    ESTIMATE_RESPONSE_SCHEMA,
)
from backend.services.estimate_parser import parse_estimate_payload
from backend.services.food_knowledge import (
    build_single_dish_ingredient_breakdown,
    retrieve_food_knowledge,
)
from backend.services.prompt_layers import build_layered_system_prompt
from backend.services.profile_service import get_profile


MULTI_FOOD_CONNECTOR_TERMS = (
    "\u52a0",
    "\u914d",
    "\u642d\u914d",
    "\u8fd8\u6709",
    "\u4ee5\u53ca",
    "\u3001",
    ",",
    "\uff0c",
    "+",
)
QUANTITY_TOKEN_RE = re.compile(
    r"[\u4e00\u4e8c\u4e24\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341\u534a\d]+"
    r"(?:\u4efd|\u7897|\u676f|\u4e2a|\u53ea|\u6839|\u5757|\u7247|\u4e32|\u76d2|\u76d8|\u52fa)"
)
NON_FOOD_HE_TERMS = (
    "\u70ed\u91cf\u548c",
    "\u80fd\u91cf\u548c",
    "\u8425\u517b\u548c",
    "\u86cb\u767d\u8d28\u548c",
    "\u78b3\u6c34\u548c",
    "\u8102\u80aa\u548c",
    "\u548c\u4e09\u5927\u8425\u517b\u7d20",
    "\u548c\u8425\u517b",
    "\u548c\u86cb\u767d\u8d28",
    "\u548c\u78b3\u6c34",
    "\u548c\u8102\u80aa",
)


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
            user_message="\u4f30\u7b97\u670d\u52a1\u6682\u672a\u914d\u7f6e\uff0c\u8bf7\u7a0d\u540e\u518d\u8bd5\u3002",
            retryable=False,
        )


class UpstreamAIError(EstimateServiceError):
    def __init__(self, message: str, *, retryable: bool) -> None:
        super().__init__(
            code="AI_UPSTREAM_ERROR",
            status_code=503,
            message=message,
            user_message="\u4f30\u7b97 AI \u670d\u52a1\u6682\u65f6\u4e0d\u53ef\u7528\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002",
            retryable=retryable,
        )


class InvalidAIResponseError(EstimateServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(
            code="AI_RESPONSE_INVALID",
            status_code=502,
            message=message,
            user_message="AI \u8fd4\u56de\u7ed3\u679c\u5f02\u5e38\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002",
            retryable=True,
        )


class IncompleteAIResponseError(EstimateServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(
            code="AI_RESPONSE_INCOMPLETE",
            status_code=502,
            message=message,
            user_message="AI \u8fd4\u56de\u7ed3\u679c\u4e0d\u5b8c\u6574\uff0c\u8bf7\u7a0d\u540e\u91cd\u8bd5\u3002",
            retryable=True,
        )


def estimate_meal(
    query: str,
    profile_id: int | None = None,
    user_id: int | None = None,
) -> EstimateResult:
    retrieved_knowledge = retrieve_food_knowledge(query, scenario="estimate")
    profile_context = _load_profile_context(profile_id, user_id)
    inferred_multi_food_count = _infer_multi_food_count(query)
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

    if _needs_multi_food_retry(parsed, inferred_multi_food_count):
        retry_raw_response = _call_ai_api(
            query,
            profile_context,
            food_knowledge_context=retrieved_knowledge.context_text if retrieved_knowledge.has_hits else None,
            force_min_items=inferred_multi_food_count,
        )
        try:
            retry_parsed = parse_estimate_payload(retry_raw_response)
            if len(retry_parsed.items) > len(parsed.items):
                parsed = retry_parsed
        except ValueError:
            pass

    parsed = _apply_single_dish_itemization(parsed, query, inferred_multi_food_count)

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
    route_rules: list[str] = [
        system_prompt.strip(),
        ESTIMATE_CAPABILITY_RULES,
        (
            "When PROFILE_CONTEXT is available, personalize assumptions and final suggestion "
            "while keeping nutrition estimate grounded in the described meal."
        ),
        "Do not recommend foods that conflict with listed allergies or avoidances.",
    ]
    if force_min_items and force_min_items > 1:
        route_rules.append(
            (
                "Important formatting rule for this request: the user likely mentioned multiple foods. "
                f"Return at least {force_min_items} distinct items in `items`, one major food per item. "
                "Do not merge multiple foods into a single item row."
            )
        )
    return build_layered_system_prompt(
        route_name="estimate",
        system_rules="\n\n".join(route_rules),
        profile_context=profile_context,
        retrieved_knowledge_context=food_knowledge_context,
        output_contract=ESTIMATE_OUTPUT_CONTRACT,
    )


def _needs_multi_food_retry(result: EstimateResult, inferred_multi_food_count: int | None) -> bool:
    if inferred_multi_food_count is None or inferred_multi_food_count < 2:
        return False
    return len(result.items) < inferred_multi_food_count


def _apply_single_dish_itemization(
    result: EstimateResult,
    query: str,
    inferred_multi_food_count: int | None,
) -> EstimateResult:
    if inferred_multi_food_count and inferred_multi_food_count > 1:
        return result

    if len(result.items) == 1:
        primary_item = result.items[0]
        dish_breakdown = build_single_dish_ingredient_breakdown(
            query,
            primary_item_name=primary_item.name,
            total_calories_text=result.total_calories,
            primary_portion_text=primary_item.portion,
            primary_protein_text=primary_item.protein,
            primary_carbs_text=primary_item.carbs,
            primary_fat_text=primary_item.fat,
        )
        if dish_breakdown:
            return result.model_copy(
                update={
                    "items": [
                        EstimateItem.model_validate(item)
                        for item in dish_breakdown
                    ],
                    "itemization_mode": "single_dish_ingredients",
                }
            )
        return result

    if len(result.items) > 1:
        return result.model_copy(update={"itemization_mode": "single_dish_ingredients"})

    return result


def _infer_multi_food_count(query: str) -> int | None:
    normalized = query.strip()
    if not normalized:
        return None

    connector_hits = _count_multi_food_connectors(normalized)
    quantity_hits = len(QUANTITY_TOKEN_RE.findall(normalized))

    if connector_hits <= 0 and quantity_hits < 2:
        return None

    inferred = max(connector_hits + 1, quantity_hits)
    return max(2, min(inferred, 3))


def _count_multi_food_connectors(query: str) -> int:
    connector_hits = sum(1 for term in MULTI_FOOD_CONNECTOR_TERMS if term in query)
    sanitized_query = query
    for term in NON_FOOD_HE_TERMS:
        sanitized_query = sanitized_query.replace(term, "")
    connector_hits += sanitized_query.count("\u548c")
    return connector_hits


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
