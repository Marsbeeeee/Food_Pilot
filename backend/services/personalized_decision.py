from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any

from backend.schemas.profile import ProfileOut
from backend.services.recommendation import check_allergen_violations


_NUMBER_RE = re.compile(r"(\d+(?:\.\d+)?)")

_FAT_LOSS_TERMS = ("减脂", "减重", "控脂", "fat loss", "lose fat", "weight loss")
_MUSCLE_GAIN_TERMS = ("增肌", "增重", "muscle gain", "build muscle", "bulk")
_MAINTAIN_TERMS = ("维持", "保持", "maintain", "maintenance")

_HIGH_PROTEIN_TERMS = ("高蛋白", "high protein", "protein")
_LOW_CARB_TERMS = ("低碳", "低碳水", "控碳", "low carb", "keto", "ketogenic")
_LOW_SUGAR_TERMS = ("控糖", "低糖", "少糖", "无糖", "low sugar", "sugar")
_VEGETARIAN_TERMS = ("素食", "vegetarian")
_VEGAN_TERMS = ("纯素", "vegan")

_AGGRESSIVE_PACE_TERMS = ("激进", "快速", "快", "aggressive", "fast")
_SLOW_PACE_TERMS = ("慢", "缓", "slow", "gentle")

_HIGH_SUGAR_LEVELS = {"全糖", "七分糖", "半糖"}
_MODERATE_SUGAR_LEVELS = {"五分糖", "少糖"}
_LARGE_PORTION_SPECS = {"大杯", "超大杯", "双人", "多人"}

_BEVERAGE_HINTS = ("奶茶", "果茶", "茶饮", "咖啡", "拿铁", "美式", "可乐", "饮品")
_FAST_FOOD_HINTS = ("汉堡", "薯条", "炸鸡", "可乐", "鸡块", "披萨")
_MEAT_HINTS = (
    "鸡", "牛", "猪", "羊", "鱼", "虾", "蟹", "贝", "培根", "火腿",
    "肉", "鸡胸", "鸡腿", "牛肉", "猪肉", "羊肉", "海鲜",
)
_DAIRY_HINTS = (
    "奶", "牛奶", "拿铁", "芝士", "奶酪", "黄油", "酸奶", "奶油", "厚乳", "鲜奶",
)
_EGG_HINTS = ("蛋", "鸡蛋", "蛋黄", "蛋白", "蛋挞")
_CARB_HEAVY_HINTS = ("米饭", "面", "面包", "汉堡", "卷饼", "粉", "米线", "薯条")

_RISK_REASON_LABELS = {
    "allergen_conflict": "与你的过敏原或限制冲突",
    "lactose_sensitive": "乳制品风险偏高",
    "diet_style_conflict": "与当前饮食风格不一致",
    "high_calorie": "单次热量占比偏高",
    "high_sugar": "糖负担偏高",
    "large_portion": "份量偏大",
    "low_protein": "蛋白质支撑偏弱",
}

_RECOMMENDATION_LABELS = {
    "recommended": "整体匹配",
    "acceptable": "可以点",
    "caution": "可点但有边界",
    "not_recommended": "不建议点",
    "needs_review": "需要复核",
}


@dataclass(slots=True)
class NutritionMetrics:
    total_calories: float | None
    protein_grams: float
    carbs_grams: float
    fat_grams: float


@dataclass(slots=True)
class PersonalizedDecision:
    recommendation_level: str
    risk_tags: list[str]
    adaptation_note: str
    adjustments: list[str]
    alternatives: list[str]
    is_personalized: bool
    personalization_note: str


def resolve_personalized_decision(
    *,
    input_summary: str,
    normalized_product: dict[str, Any],
    nutrition_items: list[dict[str, Any]],
    total_calories: str,
    confidence_level: str,
    description: str | None,
    suggestion: str | None,
    profile: ProfileOut | None = None,
    profile_requested: bool = False,
    needs_clarification: bool = False,
) -> PersonalizedDecision:
    metrics = _extract_nutrition_metrics(nutrition_items, total_calories)
    text_fragments = _collect_product_fragments(
        input_summary=input_summary,
        normalized_product=normalized_product,
        nutrition_items=nutrition_items,
        description=description,
    )
    text_corpus = " ".join(text_fragments)
    compact_text = _compact_text(text_corpus)

    risk_tags: list[str] = []
    adjustments: list[str] = []
    alternatives: list[str] = []
    blocker_reasons: list[str] = []

    goal = _normalize_goal(getattr(profile, "goal", None))
    diet_style = _normalize_diet_style(getattr(profile, "diet_style", None))
    strictness = _resolve_pace_strictness(getattr(profile, "pace", None))
    is_beverage = _is_beverage(normalized_product, compact_text)
    is_fast_food = _is_fast_food(normalized_product, compact_text)
    has_dairy = _contains_any(compact_text, _DAIRY_HINTS) or bool(normalized_product.get("milk_base"))
    has_meat = _contains_any(compact_text, _MEAT_HINTS)
    has_egg = _contains_any(compact_text, _EGG_HINTS)
    carbs_heavy = _contains_any(compact_text, _CARB_HEAVY_HINTS)
    sugar_level = str(normalized_product.get("sugar_level") or "").strip()
    size_or_spec = str(normalized_product.get("size_or_spec") or "").strip()

    if profile is not None and getattr(profile, "allergies", None):
        ok, conflicts = check_allergen_violations(text_fragments, list(profile.allergies))
        if not ok and conflicts:
            risk_tags.append("allergen_conflict")
            blocker_reasons.append("与你的过敏原或避免项直接冲突")
            adjustments.append(f"避开含 {('、'.join(conflicts[:3]))} 的版本")
            if has_dairy or is_beverage:
                alternatives.append("优先换成不含相关过敏原的纯茶、美式或定制版本")
            else:
                alternatives.append("改选不含该过敏原的替代单品")

    if profile is not None and _has_lactose_sensitive_restriction(profile) and has_dairy:
        risk_tags.append("lactose_sensitive")
        blocker_reasons.append("当前商品含乳制品，不适合乳糖限制场景")
        adjustments.append("尽量避免奶基底，优先换成无奶版本")
        if is_beverage:
            alternatives.append("改成纯茶、美式或燕麦奶版本")
        else:
            alternatives.append("改成无奶酱或非乳制品主菜")

    if _is_high_sugar_drink(
        normalized_product=normalized_product,
        compact_text=compact_text,
        total_calories=metrics.total_calories,
        carbs_grams=metrics.carbs_grams,
    ):
        risk_tags.append("high_sugar")
        adjustments.append("优先改无糖/三分糖，能换小杯就不要大杯")
        alternatives.append("换成无糖纯茶、美式或更小杯型")

    if _is_large_portion(
        normalized_product=normalized_product,
        total_calories=metrics.total_calories,
    ):
        risk_tags.append("large_portion")
        adjustments.append("把份量降一档，或和他人分食")

    if _is_high_calorie_for_context(
        total_calories=metrics.total_calories,
        goal=goal,
        kcal_target=getattr(profile, "kcal_target", None),
        strictness=strictness,
    ):
        risk_tags.append("high_calorie")
        adjustments.append("如果要更稳妥，优先缩小规格或减少高热量配料")

    if profile is not None and goal == "muscle_gain" and metrics.protein_grams < 20:
        risk_tags.append("low_protein")
        adjustments.append("补一份高蛋白来源，避免只留下空热量")
        alternatives.append("可搭配鸡胸肉、卤蛋、无糖酸奶等高蛋白配菜")

    if profile is not None:
        if diet_style in {"vegetarian", "vegan"} and has_meat:
            risk_tags.append("diet_style_conflict")
            blocker_reasons.append("当前商品含明显动物性食材")
            adjustments.append("改选豆制品、菌菇或鸡蛋类主菜")
            alternatives.append("换成豆腐碗、菌菇沙拉或全谷物主食")
        if diet_style == "vegan" and (has_dairy or has_egg):
            risk_tags.append("diet_style_conflict")
            blocker_reasons.append("当前商品含乳制品或蛋类")
            adjustments.append("改成纯素基底和无奶版本")
            alternatives.append("换成纯素沙拉、纯茶或黑咖啡")
        if diet_style == "low_carb" and (metrics.carbs_grams >= 55 or carbs_heavy):
            risk_tags.append("diet_style_conflict")
            adjustments.append("减少主食底和含糖饮料，优先蛋白质和蔬菜")
            alternatives.append("主食改沙拉底，饮料改无糖")
        if diet_style == "low_sugar" and "high_sugar" in risk_tags:
            risk_tags.append("diet_style_conflict")
        if diet_style == "high_protein" and metrics.protein_grams < 20:
            risk_tags.append("diet_style_conflict")

        if goal == "fat_loss":
            if "high_sugar" in risk_tags:
                adjustments.append("减脂阶段更适合把甜度压低，再决定是否保留奶基底")
            if is_fast_food and metrics.total_calories and metrics.total_calories >= 600:
                risk_tags.append("high_calorie")
                adjustments.append("快餐类优先换烤制/少酱版本，饮料改无糖")
                alternatives.append("可换成轻食碗、鸡胸肉卷或无糖饮料组合")

    risk_tags = _dedupe_values(risk_tags)
    adjustments = _dedupe_values(adjustments)
    alternatives = _dedupe_values(alternatives)

    recommendation_level = _resolve_recommendation_level(
        risk_tags=risk_tags,
        blocker_reasons=blocker_reasons,
        confidence_level=confidence_level,
        needs_clarification=needs_clarification,
        goal=goal,
    )

    personalization_note = _build_personalization_note(
        profile=profile,
        profile_requested=profile_requested,
        needs_clarification=needs_clarification,
    )
    adaptation_note = _build_adaptation_note(
        recommendation_level=recommendation_level,
        risk_tags=risk_tags,
        blocker_reasons=blocker_reasons,
        profile=profile,
        description=description,
        goal=goal,
        is_beverage=is_beverage,
    )

    if suggestion and suggestion.strip():
        adjustments.append(suggestion.strip())
        adjustments = _dedupe_values(adjustments)

    if recommendation_level == "recommended" and not adjustments and suggestion and suggestion.strip():
        adjustments = [suggestion.strip()]

    return PersonalizedDecision(
        recommendation_level=recommendation_level,
        risk_tags=risk_tags,
        adaptation_note=adaptation_note,
        adjustments=adjustments,
        alternatives=alternatives,
        is_personalized=profile is not None and not needs_clarification,
        personalization_note=personalization_note,
    )


def _extract_nutrition_metrics(
    items: list[dict[str, Any]],
    total_calories: str,
) -> NutritionMetrics:
    return NutritionMetrics(
        total_calories=_extract_number(total_calories),
        protein_grams=sum(_extract_number(item.get("protein")) or 0 for item in items),
        carbs_grams=sum(_extract_number(item.get("carbs")) or 0 for item in items),
        fat_grams=sum(_extract_number(item.get("fat")) or 0 for item in items),
    )


def _collect_product_fragments(
    *,
    input_summary: str,
    normalized_product: dict[str, Any],
    nutrition_items: list[dict[str, Any]],
    description: str | None,
) -> list[str]:
    fragments: list[str] = [input_summary]
    for key in (
        "brand_name",
        "category_name",
        "product_name",
        "normalized_name",
        "size_or_spec",
        "sugar_level",
        "milk_base",
        "temperature",
        "quantity",
    ):
        value = normalized_product.get(key)
        if isinstance(value, str) and value.strip():
            fragments.append(value)
    for addon in normalized_product.get("addons") or []:
        if isinstance(addon, str) and addon.strip():
            fragments.append(addon)
    for combo_item in normalized_product.get("combo_items") or []:
        if isinstance(combo_item, dict):
            name = combo_item.get("product_name")
            if isinstance(name, str) and name.strip():
                fragments.append(name)
    for item in nutrition_items:
        name = item.get("name")
        portion = item.get("portion")
        if isinstance(name, str) and name.strip():
            fragments.append(name)
        if isinstance(portion, str) and portion.strip():
            fragments.append(portion)
    if description and description.strip():
        fragments.append(description.strip())
    return [fragment for fragment in fragments if fragment]


def _normalize_goal(value: str | None) -> str | None:
    normalized = _compact_text(value)
    if not normalized:
        return None
    if _contains_any(normalized, _FAT_LOSS_TERMS):
        return "fat_loss"
    if _contains_any(normalized, _MUSCLE_GAIN_TERMS):
        return "muscle_gain"
    if _contains_any(normalized, _MAINTAIN_TERMS):
        return "maintain"
    return "general"


def _normalize_diet_style(value: str | None) -> str | None:
    normalized = _compact_text(value)
    if not normalized:
        return None
    if _contains_any(normalized, _VEGAN_TERMS):
        return "vegan"
    if _contains_any(normalized, _VEGETARIAN_TERMS):
        return "vegetarian"
    if _contains_any(normalized, _LOW_CARB_TERMS):
        return "low_carb"
    if _contains_any(normalized, _LOW_SUGAR_TERMS):
        return "low_sugar"
    if _contains_any(normalized, _HIGH_PROTEIN_TERMS):
        return "high_protein"
    return "balanced"


def _resolve_pace_strictness(value: str | None) -> str:
    normalized = _compact_text(value)
    if not normalized:
        return "moderate"
    if _contains_any(normalized, _AGGRESSIVE_PACE_TERMS):
        return "aggressive"
    if _contains_any(normalized, _SLOW_PACE_TERMS):
        return "gentle"
    return "moderate"


def _has_lactose_sensitive_restriction(profile: ProfileOut) -> bool:
    allergies = getattr(profile, "allergies", None) or []
    combined = " ".join(str(item) for item in allergies)
    normalized = _compact_text(combined)
    return any(term in normalized for term in ("乳糖", "牛奶", "乳制品", "奶制品"))


def _is_beverage(normalized_product: dict[str, Any], compact_text: str) -> bool:
    category_name = _compact_text(str(normalized_product.get("category_name") or ""))
    if any(term in category_name for term in ("茶", "咖啡", "饮品")):
        return True
    return _contains_any(compact_text, _BEVERAGE_HINTS)


def _is_fast_food(normalized_product: dict[str, Any], compact_text: str) -> bool:
    category_name = _compact_text(str(normalized_product.get("category_name") or ""))
    if "快餐" in category_name:
        return True
    return _contains_any(compact_text, _FAST_FOOD_HINTS)


def _is_high_sugar_drink(
    *,
    normalized_product: dict[str, Any],
    compact_text: str,
    total_calories: float | None,
    carbs_grams: float,
) -> bool:
    sugar_level = str(normalized_product.get("sugar_level") or "").strip()
    if sugar_level in _HIGH_SUGAR_LEVELS:
        return True
    if sugar_level and sugar_level not in {"无糖", "少糖", "微糖", "三分糖"} and total_calories is not None and total_calories >= 260:
        return True
    if sugar_level == "三分糖" and total_calories is not None and total_calories >= 280:
        return True
    if sugar_level in _MODERATE_SUGAR_LEVELS and total_calories is not None and total_calories >= 280:
        return True
    if not _is_beverage(normalized_product, compact_text):
        return False
    if total_calories is not None and total_calories >= 320:
        return True
    return carbs_grams >= 35


def _is_large_portion(
    *,
    normalized_product: dict[str, Any],
    total_calories: float | None,
) -> bool:
    size_or_spec = str(normalized_product.get("size_or_spec") or "").strip()
    quantity = str(normalized_product.get("quantity") or "").strip()
    if size_or_spec in _LARGE_PORTION_SPECS:
        return True
    if any(marker in quantity for marker in ("双人", "多人", "2", "3")) and quantity.endswith(("份", "杯", "个")):
        return True
    return total_calories is not None and total_calories >= 750


def _is_high_calorie_for_context(
    *,
    total_calories: float | None,
    goal: str | None,
    kcal_target: int | None,
    strictness: str,
) -> bool:
    if total_calories is None:
        return False

    budget = float(kcal_target or 2000)
    threshold = 700.0
    if goal == "fat_loss":
        threshold = budget * (0.35 if strictness == "aggressive" else 0.4)
    elif goal == "muscle_gain":
        threshold = budget * 0.5
    elif goal == "maintain":
        threshold = budget * 0.45

    threshold = min(max(threshold, 550.0), 900.0)
    return total_calories >= threshold


def _resolve_recommendation_level(
    *,
    risk_tags: list[str],
    blocker_reasons: list[str],
    confidence_level: str,
    needs_clarification: bool,
    goal: str | None,
) -> str:
    normalized_confidence = _compact_text(confidence_level)
    if blocker_reasons:
        return "not_recommended"
    if needs_clarification:
        return "needs_review"
    if normalized_confidence in {"low", "unknown"}:
        return "needs_review"
    if not risk_tags:
        return "recommended"

    severe_tags = {
        tag
        for tag in risk_tags
        if tag in {"high_sugar", "high_calorie", "diet_style_conflict", "lactose_sensitive"}
    }
    if goal == "fat_loss" and {"high_sugar", "high_calorie"} & severe_tags:
        return "caution"
    if len(severe_tags) >= 2:
        return "caution"
    if severe_tags:
        return "acceptable"
    return "acceptable"


def _build_personalization_note(
    *,
    profile: ProfileOut | None,
    profile_requested: bool,
    needs_clarification: bool,
) -> str:
    if needs_clarification:
        return "商品信息不足，暂未进入稳定的个体化判断。"
    if profile is None:
        if profile_requested:
            return "未命中可用 Profile，当前回退为通用结论。"
        return "未提供 Profile，当前为通用结论。"

    basis: list[str] = []
    if profile.goal:
        basis.append(profile.goal)
    if getattr(profile, "kcal_target", None):
        basis.append(f"{profile.kcal_target} kcal 目标")
    if profile.diet_style:
        basis.append(profile.diet_style)
    if profile.allergies:
        basis.append(f"避开 {('、'.join(profile.allergies[:2]))}")

    if not basis:
        return "已结合你的 Profile 做判断。"
    return f"已结合你的 {('、'.join(basis[:3]))} 做判断。"


def _build_adaptation_note(
    *,
    recommendation_level: str,
    risk_tags: list[str],
    blocker_reasons: list[str],
    profile: ProfileOut | None,
    description: str | None,
    goal: str | None,
    is_beverage: bool,
) -> str:
    if blocker_reasons:
        prefix = "结合你的当前档案，" if profile is not None else "从安全角度看，"
        return prefix + blocker_reasons[0] + "，这类商品不建议点。"

    reason_labels = [
        _RISK_REASON_LABELS[tag]
        for tag in risk_tags
        if tag in _RISK_REASON_LABELS
    ]
    reason_text = "、".join(reason_labels[:2])
    fallback_description = (description or "").strip()

    if recommendation_level == "recommended":
        if profile is not None:
            if goal == "muscle_gain":
                return "这份选择对补充能量和蛋白质更友好，整体匹配你当前目标。"
            if goal == "fat_loss":
                return "这份选择整体更容易纳入当前控制目标，边界相对清晰。"
            return "这份选择整体匹配度不错，可以作为当前场景下的稳妥选项。"
        if fallback_description:
            return f"通用判断下，这份选择整体可接受。{fallback_description}"
        return "通用判断下，这份选择整体可接受。"

    if recommendation_level == "acceptable":
        if reason_text:
            return f"这份选择可以点，但 {reason_text}，更适合先做调整。"
        if fallback_description:
            return fallback_description
        return "这份选择可以点，但更适合先做一些调整。"

    if recommendation_level == "caution":
        if reason_text:
            return f"这份选择不是完全不能点，但边界很明显：{reason_text}。"
        if is_beverage:
            return "这杯饮品不是完全不能点，但更适合先压低糖度和杯型。"
        return "这份选择不是完全不能点，但更适合控制份量和配料。"

    if fallback_description:
        return fallback_description
    return f"当前结论为 {_RECOMMENDATION_LABELS.get(recommendation_level, recommendation_level)}。"


def _extract_number(value: object) -> float | None:
    if value is None:
        return None
    matched = _NUMBER_RE.search(str(value))
    if matched is None:
        return None
    try:
        return float(matched.group(1))
    except ValueError:
        return None


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    normalized_text = _compact_text(text)
    return any(_compact_text(term) in normalized_text for term in terms)


def _compact_text(value: object) -> str:
    return "".join(str(value or "").strip().lower().split())


def _dedupe_values(values: list[str]) -> list[str]:
    deduped: list[str] = []
    seen: set[str] = set()
    for value in values:
        normalized = value.strip()
        if not normalized:
            continue
        key = normalized.lower()
        if key in seen:
            continue
        seen.add(key)
        deduped.append(normalized)
    return deduped
