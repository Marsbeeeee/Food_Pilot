import json
import re
from typing import Any
from urllib import error

from pydantic import ValidationError

from backend.config.estimate import get_estimate_ai_config
from backend.services.ai_client import call_ai
from backend.schemas.knowledge import KnowledgeReference
from backend.schemas.profile import ProfileOut
from backend.schemas.recommendation import GuidanceReply
from backend.services.food_knowledge import retrieve_food_knowledge
from backend.services.profile_service import get_profile
from backend.services.prompt_layers import build_layered_system_prompt
from backend.services.recommendation_contract import (
    GUIDANCE_MODE_RULES,
    GUIDANCE_OUTPUT_CONTRACT,
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

EXPLICIT_ALLERGY_RE = re.compile(r"对(?P<term>[^，。！？；,.!?]{1,16})过敏")
EXPLICIT_LIMIT_RE = re.compile(
    r"(?:不吃|不要吃|别吃|不能吃|不喝|别喝|不能喝|不想吃|忌口|禁忌|避开|不加|不放|别放|不要放|别推荐|不要推荐|不推荐)"
    r"(?P<term>[^，。！？；,.!?]{1,24})"
)
TERM_SPLIT_RE = re.compile(r"(?:和|跟|与|及|以及|或者|或|还有|、|,|，)")
TERM_TOKEN_RE = re.compile(r"[\u4e00-\u9fffA-Za-z0-9]{1,14}")
RESTRICTION_NOISE_TERMS = {
    "我",
    "都",
    "任何",
    "这些",
    "这种",
    "那个",
    "这个",
    "东西",
    "食物",
    "饮食",
    "推荐",
    "建议",
    "一下",
    "给我",
    "尽量",
    "最好",
}
SINGLE_CHAR_RESTRICTION_TERMS = {"辣", "糖", "盐", "酒"}
CONTRAINDICATION_RULES: dict[str, tuple[str, ...]] = {
    "痛风": ("海鲜", "动物内脏", "酒精"),
    "高尿酸": ("海鲜", "动物内脏", "酒精"),
    "高血压": ("高盐",),
    "糖尿病": ("高糖",),
    "高血糖": ("高糖",),
    "乳糖不耐": ("牛奶",),
    "麸质不耐": ("麸质",),
    "胃炎": ("辛辣", "酒精"),
    "胃溃疡": ("辛辣", "酒精"),
}
SAFETY_TERM_VARIANTS: dict[str, tuple[str, ...]] = {
    "牛肉": ("牛肉", "牛柳", "牛腩", "牛排", "肥牛", "牛肉丸"),
    "猪肉": ("猪肉", "五花肉", "里脊", "肉末"),
    "鸡肉": ("鸡肉", "鸡胸", "鸡腿", "鸡排"),
    "花生": ("花生", "花生酱", "花生碎", "花生粉"),
    "坚果": ("坚果", "花生", "杏仁", "核桃", "腰果", "榛子", "开心果"),
    "牛奶": ("牛奶", "乳制品", "奶制品", "酸奶", "奶油", "黄油", "奶酪", "芝士"),
    "海鲜": ("海鲜", "虾", "蟹", "贝类", "蛤蜊", "鱿鱼", "墨鱼"),
    "麸质": ("麸质", "小麦", "面粉", "面条", "面包", "馒头", "蛋糕", "饼干"),
    "酒精": ("酒精", "啤酒", "白酒", "红酒", "鸡尾酒"),
    "辛辣": ("辛辣", "麻辣", "香辣", "辣椒", "辣油", "辣酱"),
    "高糖": ("高糖", "含糖饮料", "甜品", "甜点", "糖浆", "奶茶", "蜂蜜"),
    "高盐": ("高盐", "咸菜", "腌菜", "腌制", "火腿", "培根"),
    "动物内脏": ("动物内脏", "内脏", "肥肠", "猪肝", "鸭肠"),
}
AVOIDANCE_CONTEXT_CUES = (
    "不含",
    "无",
    "避免",
    "避开",
    "不要",
    "别",
    "不吃",
    "不能吃",
    "不喝",
    "不能喝",
    "忌口",
    "禁忌",
    "去掉",
    "不加",
    "不放",
    "远离",
)

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
    retrieved_knowledge = retrieve_food_knowledge(query, scenario=response_mode)
    raw_response = _call_ai_api(
        query,
        response_mode=response_mode,
        profile_context=profile_context,
        food_knowledge_context=retrieved_knowledge.context_text if retrieved_knowledge.has_hits else None,
    )
    try:
        result = _parse_guidance_payload(raw_response, response_mode=response_mode)
    except (InvalidAIResponseError, IncompleteAIResponseError):
        raise
    except ValueError as exc:
        if str(exc) == "AI response is missing response":
            raise IncompleteAIResponseError(str(exc)) from exc
        raise InvalidAIResponseError(str(exc)) from exc
    except Exception as exc:
        raise InvalidAIResponseError(f"Unexpected error: {exc!s}") from exc
    if retrieved_knowledge.references:
        result = result.model_copy(
            update={
                "knowledge_refs": [
                    KnowledgeReference.model_validate(ref)
                    for ref in retrieved_knowledge.references
                ]
            }
        )
    return result


def _call_ai_api(
    query: str,
    *,
    response_mode: str,
    profile_context: str | None = None,
    food_knowledge_context: str | None = None,
) -> dict[str, Any]:
    config = get_estimate_ai_config()
    if not config.api_key:
        raise MissingAPIKeyError()

    system_prompt = _build_guidance_system_instruction(
        response_mode=response_mode,
        profile_context=profile_context,
        food_knowledge_context=food_knowledge_context,
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


def _build_guidance_system_instruction(
    response_mode: str,
    profile_context: str | None = None,
    food_knowledge_context: str | None = None,
) -> str:
    """构建推荐/文本回复的系统指令。"""
    mode_rules = GUIDANCE_MODE_RULES.get(
        response_mode,
        GUIDANCE_MODE_RULES["meal_recommendation"],
    )
    system_rules = "\n\n".join(
        [
            DEFAULT_RECOMMENDATION_SYSTEM_PROMPT,
            mode_rules,
        ]
    )
    return build_layered_system_prompt(
        route_name=response_mode,
        system_rules=system_rules,
        profile_context=profile_context,
        retrieved_knowledge_context=food_knowledge_context,
        output_contract=GUIDANCE_OUTPUT_CONTRACT,
    )


def _parse_guidance_payload(
    payload: dict[str, Any],
    *,
    response_mode: str,
) -> GuidanceReply:
    """解析 AI 返回的 JSON，支持常见别名，填充默认值。"""
    if not isinstance(payload, dict):
        raise InvalidAIResponseError("AI response is not a valid JSON object")
    defaults = DEFAULT_GUIDANCE_COPY.get(
        response_mode,
        DEFAULT_GUIDANCE_COPY["meal_recommendation"],
    )
    title = _coerce_text(
        payload.get("title")
        or payload.get("name")
        or payload.get("meal_title")
    ) or defaults["title"]
    description = _coerce_text(
        payload.get("description")
        or payload.get("reason")
        or payload.get("summary")
    ) or defaults["description"]
    response = _coerce_text(
        payload.get("response")
        or payload.get("choice")
        or payload.get("content")
        or payload.get("answer")
    )
    if not response:
        raise ValueError("AI response is missing response")
    try:
        return GuidanceReply(
            title=title,
            description=description,
            response=response,
        )
    except ValidationError as exc:
        raise InvalidAIResponseError("AI response failed schema validation") from exc


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


def _normalize_safety_text(value: str) -> str:
    return " ".join(str(value).lower().strip().split())


def _collect_text_fragments(value: Any) -> list[str]:
    text_fragments: list[str] = []

    def _collect(raw_value: Any) -> None:
        if raw_value is None:
            return
        if isinstance(raw_value, str):
            text_fragments.append(raw_value)
            return
        if isinstance(raw_value, (list, tuple, set)):
            for item in raw_value:
                _collect(item)
            return
        if isinstance(raw_value, dict):
            for nested in raw_value.values():
                _collect(nested)
            return
        if isinstance(raw_value, (int, float, bool)):
            text_fragments.append(str(raw_value))

    _collect(value)
    return text_fragments


def _split_restriction_terms(raw_terms: str) -> set[str]:
    terms: set[str] = set()
    for piece in TERM_SPLIT_RE.split(raw_terms):
        candidate = piece.strip()
        if not candidate:
            continue
        for token in TERM_TOKEN_RE.findall(candidate):
            cleaned = token.strip().lower()
            if not cleaned or cleaned in RESTRICTION_NOISE_TERMS:
                continue
            if len(cleaned) == 1 and cleaned not in SINGLE_CHAR_RESTRICTION_TERMS:
                continue
            terms.add(cleaned)
    return terms


def _extract_explicit_user_restrictions(query: str | None) -> set[str]:
    if not query:
        return set()

    normalized_query = _normalize_safety_text(query)
    restrictions: set[str] = set()

    for match in EXPLICIT_ALLERGY_RE.finditer(normalized_query):
        restrictions.update(_split_restriction_terms(match.group("term")))

    for match in EXPLICIT_LIMIT_RE.finditer(normalized_query):
        restrictions.update(_split_restriction_terms(match.group("term")))

    return restrictions


def _extract_contraindication_restrictions(query: str | None) -> set[str]:
    if not query:
        return set()

    normalized_query = _normalize_safety_text(query)
    restrictions: set[str] = set()
    for trigger, blocked_terms in CONTRAINDICATION_RULES.items():
        if trigger in normalized_query:
            restrictions.update(_normalize_safety_text(term) for term in blocked_terms)
    return restrictions


def _expand_restriction_terms(restrictions: set[str]) -> set[str]:
    expanded: set[str] = set()
    normalized_restrictions = {_normalize_safety_text(term) for term in restrictions if term}
    expanded.update(term for term in normalized_restrictions if term)

    for canonical, variants in SAFETY_TERM_VARIANTS.items():
        normalized_canonical = _normalize_safety_text(canonical)
        normalized_variants = {
            _normalize_safety_text(term)
            for term in (canonical, *variants)
            if term
        }
        if any(
            restricted and (
                restricted in normalized_variants
                or any(restricted in variant or variant in restricted for variant in normalized_variants)
            )
            for restricted in normalized_restrictions
        ):
            expanded.add(normalized_canonical)
            expanded.update(normalized_variants)

    return {term for term in expanded if term}


def _build_restriction_variant_mapping(restrictions: set[str]) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for restriction in restrictions:
        normalized = _normalize_safety_text(restriction)
        if not normalized:
            continue
        for variant in _expand_restriction_terms({normalized}):
            if variant not in mapping or len(normalized) < len(mapping[variant]):
                mapping[variant] = normalized
    return mapping


def _is_avoidance_only_context(text: str, term: str) -> bool:
    start = 0
    found = False
    safe_patterns = (
        f"不含{term}",
        f"不要{term}",
        f"别{term}",
        f"避免{term}",
        f"避开{term}",
        f"不吃{term}",
        f"不能吃{term}",
        f"不喝{term}",
        f"不能喝{term}",
        f"不加{term}",
        f"不放{term}",
        f"不推荐{term}",
        f"别推荐{term}",
        f"不要推荐{term}",
    )
    unsafe_patterns = (
        f"推荐{term}",
        f"建议{term}",
        f"吃{term}",
        f"喝{term}",
        f"加{term}",
        f"放{term}",
        f"搭配{term}",
        f"{term}更好",
    )
    while True:
        index = text.find(term, start)
        if index < 0:
            break
        found = True
        window_start = max(index - 8, 0)
        window_end = min(index + len(term) + 8, len(text))
        window = text[window_start:window_end]

        if any(pattern in window for pattern in safe_patterns):
            start = index + len(term)
            continue
        if any(pattern in window for pattern in unsafe_patterns):
            return False
        if not any(cue in window for cue in AVOIDANCE_CONTEXT_CUES):
            return False
        start = index + len(term)

    return found


def _find_restriction_conflicts(
    recommended_items: Any,
    restrictions: set[str],
) -> list[str]:
    if not restrictions:
        return []

    fragments = _collect_text_fragments(recommended_items)
    if not fragments:
        return []

    normalized_recommendation = _normalize_safety_text(" ".join(fragments))
    matched: set[str] = set()

    for term in sorted(restrictions, key=len, reverse=True):
        if term not in normalized_recommendation:
            continue
        if _is_avoidance_only_context(normalized_recommendation, term):
            continue
        matched.add(term)

    return sorted(matched, key=len, reverse=True)


def check_allergen_violations(
    recommended_items: Any,
    allergens: list[str] | tuple[str, ...],
    *,
    user_query: str | None = None,
) -> tuple[bool, list[str]]:
    """
    Check whether recommendation content conflicts with safety constraints.

    This is a pure helper and does not perform any I/O. It is intended to be
    used as a post-processing safety check on model outputs.

    Sources of safety constraints:
    1) explicit profile allergens
    2) explicit user limits in the current query (e.g. 不吃/不要/过敏)
    3) lightweight contraindication cues (e.g. 痛风/高血压/糖尿病)
    """
    normalized_allergens = {
        _normalize_safety_text(str(allergen))
        for allergen in allergens
        if allergen and str(allergen).strip()
    }
    explicit_restrictions = _extract_explicit_user_restrictions(user_query)
    contraindication_restrictions = _extract_contraindication_restrictions(user_query)

    all_restrictions = (
        normalized_allergens
        | explicit_restrictions
        | contraindication_restrictions
    )
    variant_mapping = _build_restriction_variant_mapping(all_restrictions)
    expanded_restrictions = set(variant_mapping.keys())

    if not expanded_restrictions:
        return True, []

    raw_violations = _find_restriction_conflicts(recommended_items, expanded_restrictions)
    violations: list[str] = []
    seen: set[str] = set()
    for violation in raw_violations:
        canonical = variant_mapping.get(violation, violation)
        if canonical in seen:
            continue
        seen.add(canonical)
        violations.append(canonical)

    ok = not violations
    return ok, violations
