from __future__ import annotations

import re
from typing import Any


_BRAND_CATALOG = (
    {
        "brand_id": "chagee",
        "brand_name": "霸王茶姬",
        "aliases": ("霸王茶姬", "chagee"),
        "category_id": "tea_drink",
        "category_name": "现制茶饮",
    },
    {
        "brand_id": "luckin",
        "brand_name": "瑞幸",
        "aliases": ("瑞幸", "luckin"),
        "category_id": "coffee",
        "category_name": "咖啡饮品",
    },
    {
        "brand_id": "starbucks",
        "brand_name": "星巴克",
        "aliases": ("星巴克", "starbucks"),
        "category_id": "coffee",
        "category_name": "咖啡饮品",
    },
    {
        "brand_id": "mcdonalds",
        "brand_name": "麦当劳",
        "aliases": ("麦当劳", "mcdonalds"),
        "category_id": "fast_food",
        "category_name": "西式快餐",
    },
    {
        "brand_id": "kfc",
        "brand_name": "肯德基",
        "aliases": ("肯德基", "kfc"),
        "category_id": "fast_food",
        "category_name": "西式快餐",
    },
    {
        "brand_id": "burger_king",
        "brand_name": "汉堡王",
        "aliases": ("汉堡王", "burger king", "burgerking"),
        "category_id": "fast_food",
        "category_name": "西式快餐",
    },
    {
        "brand_id": "mixue",
        "brand_name": "蜜雪冰城",
        "aliases": ("蜜雪冰城", "mixue"),
        "category_id": "tea_drink",
        "category_name": "现制茶饮",
    },
    {
        "brand_id": "heytea",
        "brand_name": "喜茶",
        "aliases": ("喜茶", "heytea"),
        "category_id": "tea_drink",
        "category_name": "现制茶饮",
    },
    {
        "brand_id": "nayuki",
        "brand_name": "奈雪的茶",
        "aliases": ("奈雪", "奈雪的茶", "nayuki"),
        "category_id": "tea_drink",
        "category_name": "现制茶饮",
    },
)

_CATEGORY_HINTS = (
    {
        "category_id": "tea_drink",
        "category_name": "现制茶饮",
        "keywords": ("奶茶", "果茶", "茶饮", "柠檬茶", "奶盖", "伯牙绝弦", "幽兰"),
    },
    {
        "category_id": "coffee",
        "category_name": "咖啡饮品",
        "keywords": ("咖啡", "拿铁", "美式", "摩卡", "生椰", "dirty", "澳白"),
    },
    {
        "category_id": "fast_food",
        "category_name": "西式快餐",
        "keywords": ("汉堡", "薯条", "炸鸡", "鸡块", "可乐", "套餐", "堡"),
    },
    {
        "category_id": "rice_meal",
        "category_name": "饭类主食",
        "keywords": ("盖饭", "炒饭", "拌饭", "套餐饭", "米饭", "饭团"),
    },
    {
        "category_id": "noodle_meal",
        "category_name": "面食主食",
        "keywords": ("面", "米线", "粉", "河粉", "拉面", "炒面", "面条"),
    },
    {
        "category_id": "light_meal",
        "category_name": "轻食沙拉",
        "keywords": ("沙拉", "轻食", "能量碗", "poke", "poke bowl"),
    },
)

_GENERIC_PRODUCT_TERMS = (
    "奶茶",
    "果茶",
    "咖啡",
    "饮品",
    "汉堡",
    "炸鸡",
    "薯条",
    "可乐",
    "套餐",
    "盖饭",
    "炒饭",
    "炒面",
    "沙拉",
)

_SOURCE_AMBIGUOUS_MARKERS = (
    "自制",
    "自家",
    "homemade",
    "home made",
)

_SUGAR_LEVEL_PATTERNS = (
    "无糖",
    "三分糖",
    "五分糖",
    "七分糖",
    "半糖",
    "少糖",
    "微糖",
    "全糖",
)

_TEMPERATURE_PATTERNS = (
    "热",
    "常温",
    "多冰",
    "少冰",
    "去冰",
    "冰",
)

_MILK_BASE_PATTERNS = (
    "鲜奶",
    "厚乳",
    "燕麦奶",
    "椰乳",
    "豆奶",
    "脱脂奶",
    "全脂奶",
)

_SPEC_PATTERNS = (
    "超大杯",
    "大杯",
    "中杯",
    "小杯",
    "单人",
    "双人",
    "多人",
)

_QUANTITY_PATTERNS = (
    r"(?:一|二|两|三|四|五|\d+)(?:杯|份|个|盒|袋|瓶|罐|杯装|人份)",
    r"(?:单人|双人|多人)(?:套餐)?",
)

_ADDON_PATTERNS = (
    r"加[^\s,，、+＋/]{1,8}",
    r"去[^\s,，、+＋/]{1,8}",
    r"少[^\s,，、+＋/]{1,8}",
)

_CONNECTOR_RE = re.compile(r"(?:\+|＋|/|／|、|,|，|和|配|搭配)")
_PARENS_RE = re.compile(r"[()（）]")
_SPACE_RE = re.compile(r"\s+")
_CALORIE_HINT_RE = re.compile(r"(热量|卡路里|多少|营养|蛋白质|碳水|脂肪|能量)")

_MISSING_FIELD_LABELS = {
    "product_subject": "product_subject",
    "product_name": "product_name",
    "combo_items": "combo_items",
}


def build_product_understanding(
    *,
    input_summary: str,
    title: str | None = None,
    items: list[dict[str, Any]] | None = None,
    clarification_reason: str | None = None,
) -> dict[str, Any]:
    normalized_input = _normalize_text(input_summary)
    normalized_title = _normalize_text(title)
    combined_text = " ".join(part for part in (normalized_input, normalized_title) if part).strip()
    compact_text = _compact_text(combined_text)

    brand = _match_brand(compact_text)
    category = _match_category(compact_text, brand)
    source_ambiguous = _contains_any(compact_text, _SOURCE_AMBIGUOUS_MARKERS)

    spec = _match_first(compact_text, _SPEC_PATTERNS)
    sugar_level = _match_first(compact_text, _SUGAR_LEVEL_PATTERNS)
    temperature = _match_first(compact_text, _TEMPERATURE_PATTERNS)
    milk_base = _match_first(compact_text, _MILK_BASE_PATTERNS)
    quantity = _match_quantity(compact_text)
    addons = _extract_addons(compact_text)

    inferred_name = _infer_product_name(
        input_summary=normalized_input,
        title=normalized_title,
        brand=brand,
        spec=spec,
        sugar_level=sugar_level,
        temperature=temperature,
    )

    normalized_name = inferred_name or normalized_title or normalized_input or "未命名输入"
    combo_items = _build_combo_items(
        input_summary=normalized_input,
        title=normalized_title,
        items=items,
        brand=brand,
    )
    product_scope = "multi_item" if combo_items else "single_item"
    item_role = "top_level_item" if product_scope == "multi_item" else "single_item"

    missing_fields: list[str] = []
    risk_tags: list[str] = []

    if clarification_reason == "missing_product_subject":
        missing_fields.append(_MISSING_FIELD_LABELS["product_subject"])
        risk_tags.append("missing_product_subject")
    elif clarification_reason == "missing_product_detail":
        missing_fields.append(_MISSING_FIELD_LABELS["product_name"])
        risk_tags.append("missing_product_detail")

    if brand is not None and _is_generic_or_missing_product_name(inferred_name, brand["brand_name"]):
        missing_fields.append(_MISSING_FIELD_LABELS["product_name"])
        risk_tags.append("missing_product_detail")

    if _looks_like_combo_request(compact_text) and len(combo_items) < 2:
        missing_fields.append(_MISSING_FIELD_LABELS["combo_items"])
        risk_tags.append("combo_incomplete")

    if source_ambiguous:
        risk_tags.append("source_ambiguous")

    missing_fields = _dedupe(missing_fields)
    risk_tags = _dedupe(risk_tags)

    match_level = _resolve_match_level(
        brand=brand,
        category=category,
        product_name=inferred_name,
        source_ambiguous=source_ambiguous,
    )
    confidence_level = _resolve_product_confidence(
        match_level=match_level,
        missing_fields=missing_fields,
        clarification_reason=clarification_reason,
    )
    needs_clarification = any(
        field in {"product_subject", "product_name", "combo_items"}
        for field in missing_fields
    )

    normalized_product = {
        "category_id": category["category_id"] if category else None,
        "category_name": category["category_name"] if category else None,
        "brand_id": brand["brand_id"] if brand else None,
        "brand_name": brand["brand_name"] if brand else None,
        "product_name": inferred_name or normalized_name,
        "normalized_name": normalized_name,
        "product_scope": product_scope,
        "item_role": item_role,
        "size_or_spec": spec,
        "addons": addons,
        "sugar_level": sugar_level,
        "temperature": temperature,
        "milk_base": milk_base,
        "quantity": quantity,
        "combo_items": combo_items,
        "missing_fields": missing_fields,
        "match_level": match_level,
    }

    clarification_questions = _build_clarification_questions(
        missing_fields=missing_fields,
        normalized_product=normalized_product,
    )

    return {
        "normalized_product": normalized_product,
        "confidence_level": confidence_level,
        "needs_clarification": needs_clarification,
        "risk_tags": risk_tags,
        "clarification_questions": clarification_questions,
    }


def _normalize_text(value: str | None) -> str:
    if value is None:
        return ""
    return _SPACE_RE.sub(" ", str(value).strip())


def _compact_text(value: str | None) -> str:
    text = _normalize_text(value).casefold()
    text = _PARENS_RE.sub(" ", text)
    return _SPACE_RE.sub(" ", text).strip()


def _contains_any(text: str, terms: tuple[str, ...]) -> bool:
    return any(term.casefold() in text for term in terms)


def _match_first(text: str, patterns: tuple[str, ...]) -> str | None:
    for pattern in patterns:
        if pattern.casefold() in text:
            return pattern
    return None


def _match_quantity(text: str) -> str | None:
    for pattern in _QUANTITY_PATTERNS:
        matched = re.search(pattern, text)
        if matched:
            return matched.group(0)
    return None


def _extract_addons(text: str) -> list[str]:
    results: list[str] = []
    excluded_markers = {
        *[pattern.casefold() for pattern in _SUGAR_LEVEL_PATTERNS],
        *[pattern.casefold() for pattern in _TEMPERATURE_PATTERNS],
    }
    for pattern in _ADDON_PATTERNS:
        for match in re.finditer(pattern, text):
            candidate = match.group(0).strip()
            if candidate.casefold() in excluded_markers:
                continue
            results.append(candidate)
    return _dedupe(results)


def _match_brand(text: str) -> dict[str, str] | None:
    best_match: dict[str, str] | None = None
    best_length = -1
    for candidate in _BRAND_CATALOG:
        for alias in candidate["aliases"]:
            alias_text = alias.casefold()
            if alias_text in text and len(alias_text) > best_length:
                best_match = candidate
                best_length = len(alias_text)
    return best_match


def _match_category(text: str, brand: dict[str, str] | None) -> dict[str, str] | None:
    if brand is not None:
        return {
            "category_id": brand["category_id"],
            "category_name": brand["category_name"],
        }

    for category in _CATEGORY_HINTS:
        if _contains_any(text, tuple(keyword.casefold() for keyword in category["keywords"])):
            return {
                "category_id": category["category_id"],
                "category_name": category["category_name"],
            }
    return None


def _infer_product_name(
    *,
    input_summary: str,
    title: str,
    brand: dict[str, str] | None,
    spec: str | None,
    sugar_level: str | None,
    temperature: str | None,
) -> str:
    candidates = [title, input_summary]
    for raw_candidate in candidates:
        cleaned = _cleanup_candidate_name(
            raw_candidate,
            brand=brand,
            spec=spec,
            sugar_level=sugar_level,
            temperature=temperature,
        )
        if cleaned:
            return cleaned
    return title or input_summary


def _cleanup_candidate_name(
    value: str,
    *,
    brand: dict[str, str] | None,
    spec: str | None,
    sugar_level: str | None,
    temperature: str | None,
) -> str:
    text = _normalize_text(value)
    if not text:
        return ""

    cleaned = text
    if brand is not None:
        for alias in brand["aliases"]:
            cleaned = re.sub(re.escape(alias), " ", cleaned, flags=re.IGNORECASE)

    for marker in (spec, sugar_level, temperature):
        if marker:
            cleaned = cleaned.replace(marker, " ")

    cleaned = _CALORIE_HINT_RE.sub(" ", cleaned)
    cleaned = re.sub(r"(大概|一下|帮我|看看|多少卡|多少热量)", " ", cleaned)
    cleaned = re.sub(r"[+＋/／,，、]", " ", cleaned)
    cleaned = _SPACE_RE.sub(" ", cleaned).strip()
    return cleaned


def _is_generic_or_missing_product_name(product_name: str, brand_name: str) -> bool:
    normalized_name = _compact_text(product_name)
    if not normalized_name:
        return True
    if normalized_name == brand_name.casefold():
        return True
    return any(term.casefold() == normalized_name for term in _GENERIC_PRODUCT_TERMS)


def _build_combo_items(
    *,
    input_summary: str,
    title: str,
    items: list[dict[str, Any]] | None,
    brand: dict[str, str] | None,
) -> list[dict[str, Any]]:
    if items and len(items) > 1:
        return [
            _build_component_payload(
                item.get("name"),
                brand=brand,
                item_role=_infer_component_role(str(item.get("name") or ""), index),
                quantity=str(item.get("portion") or "").strip() or None,
            )
            for index, item in enumerate(items)
            if str(item.get("name") or "").strip()
        ]

    combined_text = " ".join(part for part in (input_summary, title) if part).strip()
    if not _looks_like_combo_request(_compact_text(combined_text)):
        return []

    segments = [
        segment.strip()
        for segment in _CONNECTOR_RE.split(combined_text)
        if segment.strip()
    ]
    segments = [
        _cleanup_candidate_name(
            segment,
            brand=brand,
            spec=None,
            sugar_level=None,
            temperature=None,
        )
        for segment in segments
    ]
    segments = [segment for segment in segments if segment]

    if len(segments) < 2:
        return []

    return [
        _build_component_payload(
            segment,
            brand=brand,
            item_role=_infer_component_role(segment, index),
            quantity=None,
        )
        for index, segment in enumerate(_dedupe(segments))
    ]


def _build_component_payload(
    product_name: str | None,
    *,
    brand: dict[str, str] | None,
    item_role: str,
    quantity: str | None,
) -> dict[str, Any]:
    normalized_name = _normalize_text(product_name) or "未命名组成项"
    category = _match_category(_compact_text(normalized_name), brand)
    return {
        "product_name": normalized_name,
        "normalized_name": normalized_name,
        "category_name": category["category_name"] if category else None,
        "brand_name": brand["brand_name"] if brand else None,
        "item_role": item_role,
        "quantity": quantity,
    }


def _infer_component_role(name: str, index: int) -> str:
    compact_name = _compact_text(name)
    if any(term in compact_name for term in ("可乐", "雪碧", "咖啡", "奶茶", "果茶", "拿铁", "美式")):
        return "combo_drink"
    if any(term in compact_name for term in ("薯条", "鸡块", "沙拉", "蛋挞", "小食")):
        return "combo_side"
    return "main_item" if index == 0 else "combo_item"


def _looks_like_combo_request(text: str) -> bool:
    if not text:
        return False
    if "套餐" in text or "组合" in text:
        return True
    return len(_CONNECTOR_RE.findall(text)) >= 2


def _resolve_match_level(
    *,
    brand: dict[str, str] | None,
    category: dict[str, str] | None,
    product_name: str,
    source_ambiguous: bool,
) -> str:
    if source_ambiguous:
        return "source_ambiguous"
    if brand is not None and not _is_generic_or_missing_product_name(product_name, brand["brand_name"]):
        return "brand_product"
    if brand is not None:
        return "brand_only"
    if category is not None and product_name:
        return "category_product"
    if category is not None:
        return "category_only"
    if product_name:
        return "private_item"
    return "unknown"


def _resolve_product_confidence(
    *,
    match_level: str,
    missing_fields: list[str],
    clarification_reason: str | None,
) -> str:
    if clarification_reason is not None:
        return "low"
    if any(field in {"product_subject", "product_name", "combo_items"} for field in missing_fields):
        return "low"
    if match_level in {"brand_product"}:
        return "high"
    if match_level in {"category_product", "private_item", "source_ambiguous"}:
        return "medium"
    if match_level in {"brand_only", "category_only"}:
        return "low"
    return "unknown"


def _build_clarification_questions(
    *,
    missing_fields: list[str],
    normalized_product: dict[str, Any],
) -> list[str]:
    questions: list[str] = []
    if "product_subject" in missing_fields:
        questions.append("请补充明确的商品主体，例如具体商品名或套餐名。")
    if "product_name" in missing_fields:
        brand_name = normalized_product.get("brand_name")
        if isinstance(brand_name, str) and brand_name:
            questions.append(f"请补充 {brand_name} 下的具体商品名，例如具体口味或单品名。")
        else:
            questions.append("请补充更具体的商品名，避免只写品类。")
    if "combo_items" in missing_fields:
        questions.append("如果这是套餐，请补充主食、饮品和配餐构成。")
    return questions


def _dedupe(values: list[str]) -> list[str]:
    seen: set[str] = set()
    results: list[str] = []
    for value in values:
        normalized = _normalize_text(value)
        if not normalized or normalized in seen:
            continue
        seen.add(normalized)
        results.append(normalized)
    return results
