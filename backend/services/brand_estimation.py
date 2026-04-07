from __future__ import annotations

import json
import re
from functools import lru_cache
from pathlib import Path
from typing import Any, Literal

from backend.services.product_understanding import build_product_understanding


TemplateSourceType = Literal["brand_template", "category_template", "generic_template"]

_SPACE_RE = re.compile(r"\s+")
_CONFIG_PATH = Path(__file__).resolve().parents[1] / "data" / "brand_estimation_config.json"


def resolve_brand_estimation(
    *,
    input_summary: str,
    title: str | None = None,
    items: list[dict[str, Any]] | None = None,
    product_understanding: dict[str, Any] | None = None,
) -> dict[str, Any] | None:
    if product_understanding is None:
        product_understanding = build_product_understanding(
            input_summary=input_summary,
            title=title,
            items=items,
        )

    if product_understanding.get("needs_clarification"):
        return None

    normalized_product = product_understanding.get("normalized_product") or {}
    if normalized_product.get("product_scope") != "single_item":
        return None

    config = _load_estimation_config()
    template = _select_template(
        config=config,
        normalized_product=normalized_product,
        input_summary=input_summary,
        title=title,
    )
    if template is None:
        return None

    nutrition = dict(template["nutrition"])
    applied_rules: list[str] = []
    missing_configuration: list[str] = []
    query_text = " ".join(part for part in (input_summary, title) if part).strip()
    quantity_multiplier = _extract_quantity_multiplier(
        config=config,
        quantity=normalized_product.get("quantity"),
        query_text=query_text,
    )

    _apply_size_modifier(
        config=config,
        template=template,
        normalized_product=normalized_product,
        nutrition=nutrition,
        applied_rules=applied_rules,
        missing_configuration=missing_configuration,
    )
    _apply_sugar_modifier(
        config=config,
        template=template,
        normalized_product=normalized_product,
        nutrition=nutrition,
        applied_rules=applied_rules,
        missing_configuration=missing_configuration,
    )
    _apply_temperature_modifier(
        config=config,
        template=template,
        normalized_product=normalized_product,
        nutrition=nutrition,
        applied_rules=applied_rules,
    )
    _apply_milk_base_modifier(
        config=config,
        template=template,
        normalized_product=normalized_product,
        nutrition=nutrition,
        applied_rules=applied_rules,
    )
    _apply_addon_modifiers(
        config=config,
        normalized_product=normalized_product,
        nutrition=nutrition,
        applied_rules=applied_rules,
    )
    _apply_quantity_multiplier(
        quantity_multiplier=quantity_multiplier,
        nutrition=nutrition,
        applied_rules=applied_rules,
    )

    confidence = _resolve_confidence(
        normalized_product=normalized_product,
        template=template,
        missing_configuration=missing_configuration,
    )
    confidence_reasons = _build_confidence_reasons(
        config=config,
        template=template,
        confidence=confidence,
        missing_configuration=missing_configuration,
    )
    title_text = _build_title(template, normalized_product)
    item_name = _normalize_text(normalized_product.get("product_name")) or template["item_name"]
    portion_text = _build_portion(
        config=config,
        template=template,
        normalized_product=normalized_product,
        quantity_multiplier=quantity_multiplier,
    )
    description = _build_description(
        config=config,
        template=template,
        confidence=confidence,
        missing_configuration=missing_configuration,
        applied_rules=applied_rules,
    )
    suggestion = _build_suggestion(
        normalized_product=normalized_product,
        applied_rules=applied_rules,
        confidence=confidence,
    )
    fallback_order = config["fallback_order"]
    fallback_path = list(fallback_order[: fallback_order.index(template["source_type"]) + 1])

    return {
        "title": title_text,
        "description": description,
        "confidence": confidence,
        "items": [
            {
                "name": item_name,
                "portion": portion_text,
                "energy": _format_calories(nutrition["calories"]),
                "protein": _format_macro(nutrition["protein"]),
                "carbs": _format_macro(nutrition["carbs"]),
                "fat": _format_macro(nutrition["fat"]),
            }
        ],
        "total_calories": _format_calories(nutrition["calories"]),
        "suggestion": suggestion,
        "estimation_meta": {
            "source_type": template["source_type"],
            "source_label": template["source_label"],
            "template_id": template["template_id"],
            "hit_level": template["source_type"].replace("_template", ""),
            "fallback_path": fallback_path,
            "confidence_reasons": confidence_reasons,
            "applied_rules": applied_rules,
            "missing_configuration": missing_configuration,
        },
    }


@lru_cache(maxsize=1)
def _load_estimation_config() -> dict[str, Any]:
    with _CONFIG_PATH.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload if isinstance(payload, dict) else {}


def _select_template(
    *,
    config: dict[str, Any],
    normalized_product: dict[str, Any],
    input_summary: str,
    title: str | None,
) -> dict[str, Any] | None:
    brand_id = _normalize_text(normalized_product.get("brand_id"))
    category_id = _normalize_text(normalized_product.get("category_id"))
    product_name = _compact_text(normalized_product.get("product_name"))
    normalized_name = _compact_text(normalized_product.get("normalized_name"))
    combined_text = _compact_text(" ".join(part for part in (input_summary, title) if part))
    templates = config.get("templates") or {}

    for template in templates.get("brand", []):
        if brand_id != template.get("brand_id"):
            continue
        if _template_matches_product(template, product_name, normalized_name, combined_text):
            return template

    for template in templates.get("category", []):
        if category_id != template.get("category_id"):
            continue
        if _template_matches_product(template, product_name, normalized_name, combined_text):
            return template

    if _is_generic_product_name(config=config, value=product_name):
        for template in templates.get("generic", []):
            if category_id == template.get("category_id"):
                return template
    return None


def _template_matches_product(
    template: dict[str, Any],
    product_name: str,
    normalized_name: str,
    combined_text: str,
) -> bool:
    for keyword in template.get("product_keywords", []):
        compact_keyword = _compact_text(keyword)
        if compact_keyword and (
            compact_keyword in product_name
            or compact_keyword in normalized_name
            or compact_keyword in combined_text
        ):
            return True
    return False


def _apply_size_modifier(
    *,
    config: dict[str, Any],
    template: dict[str, Any],
    normalized_product: dict[str, Any],
    nutrition: dict[str, float],
    applied_rules: list[str],
    missing_configuration: list[str],
) -> None:
    category_id = _normalize_text(template.get("category_id"))
    size_modifiers = ((config.get("modifiers") or {}).get("size") or {})
    if category_id not in size_modifiers:
        return

    default_size = _normalize_text(template.get("default_size"))
    size_or_spec = _normalize_text(normalized_product.get("size_or_spec"))
    if not size_or_spec:
        if default_size:
            missing_configuration.append("size_or_spec")
        return

    category_map = size_modifiers[category_id]
    resolved_size = size_or_spec if size_or_spec in category_map else default_size
    if not resolved_size or resolved_size not in category_map:
        return

    delta = float(category_map[resolved_size]) - float(category_map.get(default_size, 0.0))
    if delta == 0:
        return

    nutrition["calories"] += delta
    nutrition["carbs"] += round(delta / 12.0, 1)
    applied_rules.append(f"规格：{resolved_size}（{_format_delta(delta)} kcal）")


def _apply_sugar_modifier(
    *,
    config: dict[str, Any],
    template: dict[str, Any],
    normalized_product: dict[str, Any],
    nutrition: dict[str, float],
    applied_rules: list[str],
    missing_configuration: list[str],
) -> None:
    if not _is_drink_category(config=config, category_id=template.get("category_id")):
        return

    sugar_modifiers = ((config.get("modifiers") or {}).get("sugar") or {})
    default_sugar_level = _normalize_text(template.get("default_sugar_level"))
    sugar_level = _normalize_text(normalized_product.get("sugar_level"))
    if not sugar_level:
        if default_sugar_level:
            missing_configuration.append("sugar_level")
        return

    resolved_sugar_level = sugar_level if sugar_level in sugar_modifiers else default_sugar_level
    if not resolved_sugar_level:
        return

    delta = float(sugar_modifiers[resolved_sugar_level]) - float(
        sugar_modifiers.get(default_sugar_level, 0.0)
    )
    if delta == 0:
        return

    nutrition["calories"] += delta
    nutrition["carbs"] += round(delta / 4.0, 1)
    applied_rules.append(f"糖度：{resolved_sugar_level}（{_format_delta(delta)} kcal）")


def _apply_temperature_modifier(
    *,
    config: dict[str, Any],
    template: dict[str, Any],
    normalized_product: dict[str, Any],
    nutrition: dict[str, float],
    applied_rules: list[str],
) -> None:
    if not _is_drink_category(config=config, category_id=template.get("category_id")):
        return

    temperature_modifiers = ((config.get("modifiers") or {}).get("temperature") or {})
    default_temperature = _normalize_text(template.get("default_temperature"))
    temperature = _normalize_text(normalized_product.get("temperature"))
    if not temperature:
        return

    resolved_temperature = (
        temperature if temperature in temperature_modifiers else default_temperature
    )
    if not resolved_temperature:
        return

    delta = float(temperature_modifiers[resolved_temperature]) - float(
        temperature_modifiers.get(default_temperature, 0.0)
    )
    if delta == 0:
        return

    nutrition["calories"] += delta
    nutrition["carbs"] += round(delta / 10.0, 1)
    applied_rules.append(f"冰量/温度：{resolved_temperature}（{_format_delta(delta)} kcal）")


def _apply_milk_base_modifier(
    *,
    config: dict[str, Any],
    template: dict[str, Any],
    normalized_product: dict[str, Any],
    nutrition: dict[str, float],
    applied_rules: list[str],
) -> None:
    if not _is_drink_category(config=config, category_id=template.get("category_id")):
        return

    milk_base_modifiers = ((config.get("modifiers") or {}).get("milk_base") or {})
    milk_base = _normalize_text(normalized_product.get("milk_base"))
    if not milk_base or milk_base not in milk_base_modifiers:
        return

    default_milk_base = _normalize_text(template.get("default_milk_base"))
    modifier = dict(milk_base_modifiers[milk_base])
    if default_milk_base and default_milk_base in milk_base_modifiers:
        for nutrient_name, value in milk_base_modifiers[default_milk_base].items():
            modifier[nutrient_name] = float(modifier.get(nutrient_name, 0.0)) - float(value)

    if not any(modifier.values()):
        return

    for nutrient_name, delta in modifier.items():
        nutrition[nutrient_name] += float(delta)
    applied_rules.append(f"奶基底：{milk_base}（{_format_delta(float(modifier['calories']))} kcal）")


def _apply_addon_modifiers(
    *,
    config: dict[str, Any],
    normalized_product: dict[str, Any],
    nutrition: dict[str, float],
    applied_rules: list[str],
) -> None:
    addons = normalized_product.get("addons") or []
    addon_modifiers = ((config.get("modifiers") or {}).get("addon") or {})
    for addon in addons:
        normalized_addon = _normalize_text(addon)
        if not normalized_addon:
            continue

        modifier = _resolve_addon_modifier(addon_modifiers=addon_modifiers, addon=normalized_addon)
        if modifier is None:
            continue

        multiplier = -1.0 if normalized_addon.startswith("去") else 1.0
        for nutrient_name, delta in modifier.items():
            nutrition[nutrient_name] += float(delta) * multiplier
        applied_rules.append(
            f"{normalized_addon}（{_format_delta(float(modifier['calories']) * multiplier)} kcal）"
        )


def _apply_quantity_multiplier(
    *,
    quantity_multiplier: float,
    nutrition: dict[str, float],
    applied_rules: list[str],
) -> None:
    if quantity_multiplier <= 1:
        return

    for nutrient_name in ("calories", "protein", "carbs", "fat"):
        nutrition[nutrient_name] *= quantity_multiplier
    applied_rules.append(f"份量：x{_format_count(quantity_multiplier)}")


def _resolve_confidence(
    *,
    normalized_product: dict[str, Any],
    template: dict[str, Any],
    missing_configuration: list[str],
) -> str:
    source_type = template["source_type"]
    if source_type == "generic_template":
        return "low"

    product_name = _compact_text(normalized_product.get("product_name"))
    if source_type == "category_template":
        if _is_generic_product_name(config=_load_estimation_config(), value=product_name):
            return "low"
        return "medium"

    if missing_configuration:
        return "medium"
    return "high"


def _build_confidence_reasons(
    *,
    config: dict[str, Any],
    template: dict[str, Any],
    confidence: str,
    missing_configuration: list[str],
) -> list[str]:
    template_level_labels = config.get("template_level_labels") or {}
    reasons = [
        f"估算依据：{template_level_labels[template['source_type']]}，来源 {template['source_label']}。",
    ]
    if missing_configuration:
        reasons.append(f"关键配置缺失：{', '.join(missing_configuration)}，已按默认值估算。")
    elif confidence == "high":
        reasons.append("规格与主体信息明确，结果可按高置信处理。")
    elif confidence == "medium":
        reasons.append("已命中稳定模板，但仍有局部配置按默认值处理。")
    else:
        reasons.append("仅能走通用回退，结果适合参考，不应视为精确品牌值。")
    return reasons


def _build_title(template: dict[str, Any], normalized_product: dict[str, Any]) -> str:
    brand_name = _normalize_text(normalized_product.get("brand_name"))
    product_name = _normalize_text(normalized_product.get("product_name"))
    if brand_name and product_name and not product_name.startswith(brand_name):
        return f"{brand_name} {product_name}"
    return product_name or template["title"]


def _build_portion(
    *,
    config: dict[str, Any],
    template: dict[str, Any],
    normalized_product: dict[str, Any],
    quantity_multiplier: float,
) -> str:
    size_or_spec = _normalize_text(normalized_product.get("size_or_spec"))
    base_portion = template["portion"]
    prefix = f"{size_or_spec} " if size_or_spec else ""
    if quantity_multiplier > 1:
        unit = _extract_primary_unit(config=config, value=base_portion)
        return f"{_format_count(quantity_multiplier)} {unit}"
    return f"{prefix}{base_portion}".strip()


def _build_description(
    *,
    config: dict[str, Any],
    template: dict[str, Any],
    confidence: str,
    missing_configuration: list[str],
    applied_rules: list[str],
) -> str:
    template_level_labels = config.get("template_level_labels") or {}
    base = f"{template_level_labels[template['source_type']]}，来源 {template['source_label']}。"
    if missing_configuration:
        return (
            f"{base} 当前缺少 {', '.join(missing_configuration)}，已按模板默认配置给出 {confidence} 置信估算。"
        )
    if applied_rules:
        return f"{base} 已应用配置修正：{'；'.join(applied_rules)}。"
    return f"{base} 当前未触发额外修正规则。"


def _build_suggestion(
    *,
    normalized_product: dict[str, Any],
    applied_rules: list[str],
    confidence: str,
) -> str:
    sugar_level = _normalize_text(normalized_product.get("sugar_level"))
    addon_text = " ".join(normalized_product.get("addons") or [])
    if sugar_level in {"全糖", "七分糖"} or any(
        token in addon_text for token in ("珍珠", "奶盖", "芝士", "奥利奥")
    ):
        return "如果想把热量压低一点，优先考虑降糖或去掉高热量加料。"
    if confidence == "low":
        return "如果要提高准确度，建议补充更具体的商品名、规格或配置。"
    if applied_rules:
        return "当前结果已包含规格与配置修正，可直接用于点单前的快速比较。"
    return "当前估算适合作为点单前的基线参考。"


def _resolve_addon_modifier(
    *,
    addon_modifiers: dict[str, dict[str, float]],
    addon: str,
) -> dict[str, float] | None:
    normalized = addon[1:] if addon[:1] in {"加", "去"} else addon
    for keyword, modifier in addon_modifiers.items():
        if keyword in normalized:
            return modifier
    return None


def _extract_quantity_multiplier(
    *,
    config: dict[str, Any],
    quantity: object,
    query_text: str,
) -> float:
    normalized_quantity = _normalize_text(quantity)
    if normalized_quantity:
        parsed = _parse_quantity_token(config=config, value=normalized_quantity)
        if parsed is not None:
            return parsed

    compact_query = _compact_text(query_text)
    for unit in config.get("quantity_units", []):
        matched = re.search(rf"(\d+|一|二|两|三|四|五){unit}", compact_query)
        if not matched:
            continue
        parsed = _parse_quantity_token(config=config, value=matched.group(1))
        if parsed is not None:
            return parsed
    return 1.0


def _parse_quantity_token(
    *,
    config: dict[str, Any],
    value: str,
) -> float | None:
    normalized = _normalize_text(value)
    if not normalized:
        return None

    digit_match = re.search(r"\d+(?:\.\d+)?", normalized)
    if digit_match:
        return max(1.0, float(digit_match.group(0)))

    for token, numeric in (config.get("chinese_numbers") or {}).items():
        if token in normalized:
            return float(numeric)
    return None


def _extract_primary_unit(
    *,
    config: dict[str, Any],
    value: str,
) -> str:
    for unit in config.get("quantity_units", []):
        if unit in value:
            return unit
    return "份"


def _format_calories(value: float) -> str:
    return f"{round(max(value, 0.0))} kcal"


def _format_macro(value: float) -> str:
    clamped = max(value, 0.0)
    if abs(clamped - round(clamped)) < 0.05:
        return f"{int(round(clamped))} g"
    return f"{clamped:.1f} g"


def _format_delta(value: float) -> str:
    rounded = round(value)
    return f"+{rounded}" if rounded > 0 else str(rounded)


def _format_count(value: float) -> str:
    if abs(value - round(value)) < 0.05:
        return str(int(round(value)))
    return f"{value:.1f}"


def _normalize_text(value: object) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _compact_text(value: object) -> str:
    text = _normalize_text(value).casefold()
    return _SPACE_RE.sub(" ", text).strip()


def _is_drink_category(*, config: dict[str, Any], category_id: object) -> bool:
    normalized_category_id = _normalize_text(category_id)
    return normalized_category_id in set(config.get("drink_category_ids", []))


def _is_generic_product_name(*, config: dict[str, Any], value: str) -> bool:
    generic_product_names = {str(name).casefold() for name in config.get("generic_product_names", [])}
    return value in generic_product_names
