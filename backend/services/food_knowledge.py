import json
import logging
import math
import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any

from backend.config.food_knowledge import get_food_knowledge_config

logger = logging.getLogger(__name__)

CHINESE_CHAR_RE = re.compile(r"[\u4e00-\u9fff]")
NON_TEXT_RE = re.compile(r"[^0-9a-z\u4e00-\u9fff]+")
FLOAT_RE = re.compile(r"(\d+(?:\.\d+)?)")
GRAM_RE = re.compile(r"(\d+(?:\.\d+)?)\s*(?:g|克)", re.IGNORECASE)
QUANTITY_NOISE_TERMS = (
    "一大碗",
    "一小碗",
    "一碗",
    "一份",
    "一个",
    "一杯",
    "一盘",
    "一盒",
    "一根",
    "一笼",
    "两个",
    "两根",
    "大杯",
    "中杯",
    "小杯",
)
QUERY_INTENT_NOISE_TERMS = (
    "大概多少热量",
    "大概多少卡路里",
    "大概多少卡",
    "多少热量",
    "多少卡路里",
    "多少卡",
    "热量高吗",
    "热量高不高",
    "适不适合减脂",
    "更适合减脂",
    "更适合控糖",
    "有没有更健康的平替",
    "有没有更健康的替代",
    "有没有更轻的点法",
    "外卖怎么点更稳妥",
    "是不是更高热量",
    "是不是很油",
    "会不会太多",
    "适合当早餐吗",
    "还能喝吗",
    "大概",
    "多少",
    "热量",
    "卡路里",
    "推荐",
    "平替",
    "替代",
    "点法",
    "怎么点",
    "适合",
    "减脂",
    "控糖",
    "比较",
    "对比",
    "哪个",
    "还是",
    "会不会",
    "是不是",
    "高吗",
    "吗",
)
COMPARISON_HINT_TERMS = ("和", "还是", "哪个", "对比", "比较", "选哪个")
BEVERAGE_HINT_TERMS = ("茶", "咖啡", "拿铁", "美式", "豆浆", "甘露", "奶茶")
DISH_SHAPE_HINT_TERMS = ("面", "粉", "饭", "粥", "馍", "饼", "卷", "包", "锅", "鱼", "鸡")
SYNONYM_REPLACEMENTS = (
    ("波霸", "珍珠"),
    ("啵啵", "珍珠"),
    ("豆腐花", "豆腐脑"),
    ("豆花", "豆腐脑"),
    ("番茄", "西红柿"),
    ("青瓜", "黄瓜"),
    ("云吞", "馄饨"),
)
MODIFIER_GROUPS = {
    "low_sugar": ("低糖", "少糖", "半糖", "三分糖", "微糖", "无糖"),
    "clear_broth": ("清汤",),
    "fried": ("炸", "油炸"),
    "spicy": ("麻辣", "香辣"),
    "iced": ("冰",),
    "hot": ("热",),
}


@dataclass(frozen=True)
class FoodKnowledgeSource:
    source_id: str
    name: str
    source_type: str
    updated_at: str | None


@dataclass(frozen=True)
class FoodKnowledgeEntry:
    entry_id: str
    canonical_name: str
    aliases: tuple[str, ...]
    category: str
    nutrition_per_100g: dict[str, float]
    portion_hints: tuple[dict[str, Any], ...]
    cooking_notes: str
    source_ids: tuple[str, ...]
    updated_at: str | None
    ingredient_breakdown: tuple[dict[str, Any], ...]

    @property
    def search_terms(self) -> tuple[str, ...]:
        return (self.canonical_name, *self.aliases)


@dataclass(frozen=True)
class ScoredKnowledgeEntry:
    entry: FoodKnowledgeEntry
    score: float
    matched_terms: tuple[str, ...]


@dataclass(frozen=True)
class RetrievedKnowledge:
    context_text: str
    references: list[dict[str, str]]
    hit_count: int
    reason: str

    @property
    def has_hits(self) -> bool:
        return self.hit_count > 0


@dataclass(frozen=True)
class FoodKnowledgeDataset:
    version: str
    sources: dict[str, FoodKnowledgeSource]
    foods: tuple[FoodKnowledgeEntry, ...]


@dataclass(frozen=True)
class PreparedSearchText:
    normalized: str
    canonical: str
    core: str
    chars: frozenset[str]
    ngrams: frozenset[str]
    modifiers: frozenset[str]


@dataclass(frozen=True)
class QueryFeatures(PreparedSearchText):
    has_comparison_hint: bool
    has_beverage_hint: bool
    has_dish_hint: bool


def retrieve_food_knowledge(
    query: str,
    *,
    scenario: str,
) -> RetrievedKnowledge:
    config = get_food_knowledge_config()
    if not config.enabled:
        return RetrievedKnowledge("", [], 0, "disabled")

    normalized_query = _normalize_text(query)
    if not normalized_query:
        return RetrievedKnowledge("", [], 0, "empty_query")

    if config.only_chinese and not CHINESE_CHAR_RE.search(query):
        return RetrievedKnowledge("", [], 0, "non_chinese_query")

    try:
        dataset = _load_dataset(config.data_path)
    except Exception as exc:
        logger.warning("Food knowledge dataset unavailable: %s", exc)
        return RetrievedKnowledge("", [], 0, "dataset_unavailable")

    scored = _score_entries(dataset.foods, normalized_query, scenario=scenario)
    shortlisted = [item for item in scored if item.score >= config.min_score][: config.top_k]
    if not shortlisted:
        return RetrievedKnowledge("", [], 0, "no_match")

    references = _build_references(shortlisted, dataset.sources)
    context_text = _build_context(shortlisted, references, max_chars=config.max_context_chars)
    return RetrievedKnowledge(
        context_text=context_text,
        references=references,
        hit_count=len(shortlisted),
        reason="ok",
    )


def build_single_dish_ingredient_breakdown(
    query: str,
    *,
    primary_item_name: str,
    total_calories_text: str,
    primary_portion_text: str | None = None,
) -> list[dict[str, str]] | None:
    config = get_food_knowledge_config()
    if not config.enabled:
        return None

    normalized_query = _normalize_text(query)
    normalized_primary_item = _normalize_text(primary_item_name)
    if not normalized_query and not normalized_primary_item:
        return None

    total_calories_value = _extract_float(total_calories_text)
    if total_calories_value is None or total_calories_value <= 0:
        return None

    try:
        dataset = _load_dataset(config.data_path)
    except Exception as exc:
        logger.warning("Food knowledge dataset unavailable: %s", exc)
        return None

    target_dish = _find_best_dish_for_breakdown(
        dataset.foods,
        normalized_query=normalized_query,
        normalized_primary_item=normalized_primary_item,
    )
    if target_dish is None or len(target_dish.ingredient_breakdown) < 2:
        return None

    total_grams = _extract_grams(primary_portion_text) or _extract_default_portion_grams(target_dish)
    food_lookup = _build_food_lookup(dataset.foods)
    components = _render_breakdown_components(
        target_dish=target_dish,
        total_calories_value=total_calories_value,
        total_grams=total_grams,
        food_lookup=food_lookup,
    )
    return components if len(components) >= 2 else None


@lru_cache(maxsize=4)
def _load_dataset(path: Path) -> FoodKnowledgeDataset:
    payload = json.loads(path.read_text(encoding="utf-8"))
    sources_payload = payload.get("sources", [])
    foods_payload = payload.get("foods", [])

    sources: dict[str, FoodKnowledgeSource] = {}
    for source in sources_payload:
        if not isinstance(source, dict):
            continue
        source_id = str(source.get("id", "")).strip()
        if not source_id:
            continue
        sources[source_id] = FoodKnowledgeSource(
            source_id=source_id,
            name=str(source.get("name", "")).strip() or source_id,
            source_type=str(source.get("type", "")).strip() or "unknown",
            updated_at=_optional_text(source.get("updated_at")),
        )

    foods: list[FoodKnowledgeEntry] = []
    for food in foods_payload:
        if not isinstance(food, dict):
            continue
        canonical_name = _optional_text(food.get("canonical_name"))
        if not canonical_name:
            continue
        entry_id = _optional_text(food.get("id")) or canonical_name
        aliases = tuple(
            alias
            for alias in (
                _optional_text(item)
                for item in food.get("aliases", [])
                if isinstance(item, str) or item is not None
            )
            if alias
        )
        nutrition_payload = food.get("nutrition_per_100g")
        nutrition_per_100g = _normalize_nutrition(nutrition_payload if isinstance(nutrition_payload, dict) else {})
        if not nutrition_per_100g:
            continue

        portion_hints_raw = food.get("portion_hints", [])
        portion_hints = tuple(
            hint
            for hint in portion_hints_raw
            if isinstance(hint, dict) and _optional_text(hint.get("name"))
        )
        source_ids = tuple(
            source_id
            for source_id in (
                _optional_text(item)
                for item in food.get("source_ids", [])
                if isinstance(item, str) or item is not None
            )
            if source_id
        )
        ingredient_breakdown = _normalize_ingredient_breakdown(food.get("ingredient_breakdown"))
        foods.append(
            FoodKnowledgeEntry(
                entry_id=entry_id,
                canonical_name=canonical_name,
                aliases=aliases,
                category=_optional_text(food.get("category")) or "unknown",
                nutrition_per_100g=nutrition_per_100g,
                portion_hints=portion_hints,
                cooking_notes=_optional_text(food.get("cooking_notes")) or "",
                source_ids=source_ids,
                updated_at=_optional_text(food.get("updated_at")),
                ingredient_breakdown=ingredient_breakdown,
            )
        )

    version = _optional_text(payload.get("version")) or "unknown"
    return FoodKnowledgeDataset(
        version=version,
        sources=sources,
        foods=tuple(foods),
    )


def _normalize_nutrition(raw: dict[str, Any]) -> dict[str, float]:
    keys = ("kcal", "protein_g", "carbs_g", "fat_g")
    normalized: dict[str, float] = {}
    for key in keys:
        value = raw.get(key)
        try:
            number = float(value)
        except (TypeError, ValueError):
            return {}
        if math.isnan(number) or number < 0:
            return {}
        normalized[key] = number
    return normalized


def _score_entries(
    entries: tuple[FoodKnowledgeEntry, ...],
    normalized_query: str,
    *,
    scenario: str,
    scorer: str = "enhanced",
) -> list[ScoredKnowledgeEntry]:
    ranked: list[ScoredKnowledgeEntry] = []
    query_features = _prepare_query_features(normalized_query)
    for entry in entries:
        if scorer == "legacy":
            score, matched_terms = _score_entry_legacy(
                entry,
                normalized_query,
                query_chars=set(normalized_query),
                scenario=scenario,
            )
        else:
            score, matched_terms = _score_entry(
                entry,
                query_features,
                scenario=scenario,
            )
        if score <= 0:
            continue
        ranked.append(ScoredKnowledgeEntry(entry=entry, score=score, matched_terms=matched_terms))
    ranked.sort(key=lambda item: (-item.score, item.entry.canonical_name))
    return ranked


def _score_entry(
    entry: FoodKnowledgeEntry,
    query: QueryFeatures,
    *,
    scenario: str,
) -> tuple[float, tuple[str, ...]]:
    best_score = 0.0
    best_term_len = 0
    matched_terms: list[str] = []
    strong_matches = 0

    for term in entry.search_terms:
        prepared_term = _prepare_term_features(term)
        term_score = _score_term_against_query(query, prepared_term)
        if term_score >= 2.6:
            matched_terms.append(term)
            strong_matches += 1
        if term_score > best_score:
            best_score = term_score
            best_term_len = len(prepared_term.core or prepared_term.canonical)

    if best_score <= 0:
        return 0.0, ()

    score = best_score + _category_boost(entry.category, scenario=scenario, query=query)
    if strong_matches > 1:
        score += min(0.9, 0.25 * (strong_matches - 1))
    if best_term_len >= 4:
        score += 0.35
    score += _query_alignment_boost(entry, query)
    score -= _generic_partial_penalty(entry, query, best_term_len)
    return max(score, 0.0), tuple(dict.fromkeys(matched_terms))


def _score_entry_legacy(
    entry: FoodKnowledgeEntry,
    normalized_query: str,
    *,
    query_chars: set[str],
    scenario: str,
) -> tuple[float, tuple[str, ...]]:
    score = 0.0
    matched: list[str] = []
    terms = entry.search_terms

    for term in terms:
        normalized_term = _normalize_text(term)
        if not normalized_term:
            continue
        if normalized_term in normalized_query:
            score += 2.8 + min(len(normalized_term) * 0.15, 1.6)
            matched.append(term)

    if not matched:
        best_overlap = 0.0
        for term in terms:
            normalized_term = _normalize_text(term)
            if not normalized_term:
                continue
            term_chars = set(normalized_term)
            overlap = _dice_similarity(query_chars, term_chars)
            if overlap > best_overlap:
                best_overlap = overlap
        if best_overlap >= 0.55:
            score += best_overlap * 2.2

    score += _legacy_category_boost(entry.category, scenario=scenario)

    if matched:
        longest_match = max((len(_normalize_text(term)) for term in matched), default=0)
        if longest_match >= 3:
            score += 0.8
        if "一碗" in normalized_query and entry.category in {"staple", "dish"}:
            score += 0.3
        if "推荐" in normalized_query and entry.category in {"protein", "dish"}:
            score += 0.2

    return score, tuple(dict.fromkeys(matched))


def _category_boost(category: str, *, scenario: str, query: QueryFeatures) -> float:
    if scenario == "estimate":
        if category in {"dish", "snack", "staple", "drink"}:
            score = 0.42
        elif category == "protein":
            score = 0.16
        else:
            score = 0.08
    elif scenario in {"meal_recommendation", "text"}:
        if category in {"dish", "snack", "drink"}:
            score = 0.45
        elif category == "staple":
            score = 0.28
        elif category == "protein":
            score = 0.14
        else:
            score = 0.08
    else:
        score = 0.0

    if query.has_comparison_hint and category in {"dish", "snack", "drink", "staple"}:
        score += 0.12
    if query.has_beverage_hint and category == "drink":
        score += 0.18
    return score


def _legacy_category_boost(category: str, *, scenario: str) -> float:
    if scenario == "estimate":
        if category in {"dish", "staple"}:
            return 0.25
        return 0.1
    if scenario in {"meal_recommendation", "text"}:
        if category in {"protein", "dish", "drink"}:
            return 0.25
        return 0.08
    return 0.0


def _dice_similarity(left: set[str], right: set[str]) -> float:
    if not left or not right:
        return 0.0
    intersection = len(left.intersection(right))
    return (2.0 * intersection) / (len(left) + len(right))


def _score_term_against_query(query: QueryFeatures, term: PreparedSearchText) -> float:
    score = 0.0
    strongest_term = term.core or term.canonical
    strongest_query = query.core or query.canonical
    if not strongest_term:
        return 0.0

    if strongest_query and strongest_term == strongest_query:
        score += 8.2
    elif strongest_query and strongest_term in strongest_query:
        score += 5.6 + min(len(strongest_term) * 0.18, 1.8)
    elif term.canonical and term.canonical in query.canonical:
        score += 4.0 + min(len(term.canonical) * 0.12, 1.3)
    elif strongest_query and strongest_query in strongest_term:
        score += 3.2 + min(len(strongest_query) * 0.16, 1.2)

    ngram_recall = _overlap_ratio(query.ngrams, term.ngrams)
    ngram_precision = _overlap_ratio(term.ngrams, query.ngrams)
    if ngram_recall >= 0.34 or ngram_precision >= 0.2:
        score += ngram_recall * 2.7 + ngram_precision * 1.5

    dice = _dice_similarity(set(query.chars), set(term.chars))
    if dice >= 0.45:
        score += dice * 1.1

    modifier_alignment = _modifier_alignment_score(query.modifiers, term.modifiers)
    score += modifier_alignment

    if len(strongest_term) <= 2 and len(strongest_query) >= 4 and strongest_term not in strongest_query:
        score -= 0.8
    return max(score, 0.0)


def _query_alignment_boost(entry: FoodKnowledgeEntry, query: QueryFeatures) -> float:
    score = 0.0
    if query.has_comparison_hint and entry.category in {"dish", "snack", "drink", "staple"}:
        score += 0.18
    if query.has_beverage_hint and entry.category == "drink":
        score += 0.22
    if query.has_dish_hint and entry.category in {"dish", "snack", "staple"}:
        score += 0.16
    return score


def _generic_partial_penalty(
    entry: FoodKnowledgeEntry,
    query: QueryFeatures,
    best_term_len: int,
) -> float:
    penalty = 0.0
    if query.has_comparison_hint and entry.category == "protein":
        penalty += 0.28
    if query.has_dish_hint and entry.category in {"protein", "vegetable", "fruit", "fat", "nut"}:
        penalty += 0.22
    if len(query.core) >= 5 and best_term_len <= 2:
        penalty += 0.18
    return penalty


def _modifier_alignment_score(query_modifiers: frozenset[str], term_modifiers: frozenset[str]) -> float:
    if not query_modifiers:
        return 0.0
    shared = len(query_modifiers.intersection(term_modifiers))
    if shared:
        return 0.45 * shared
    return -0.18 if term_modifiers else 0.0


def _overlap_ratio(left: frozenset[str], right: frozenset[str]) -> float:
    if not left or not right:
        return 0.0
    overlap = len(left.intersection(right))
    return overlap / len(right)


def _prepare_query_features(normalized_query: str) -> QueryFeatures:
    canonical = _canonicalize_synonyms(normalized_query)
    quantity_stripped = _strip_known_terms(canonical, QUANTITY_NOISE_TERMS)
    core = _strip_known_terms(quantity_stripped, QUERY_INTENT_NOISE_TERMS)
    core = core or quantity_stripped or canonical
    return QueryFeatures(
        normalized=normalized_query,
        canonical=canonical,
        core=core,
        chars=frozenset(core),
        ngrams=frozenset(_build_ngrams(core)),
        modifiers=frozenset(_extract_modifiers(canonical)),
        has_comparison_hint=any(term in canonical for term in COMPARISON_HINT_TERMS),
        has_beverage_hint=any(term in canonical for term in BEVERAGE_HINT_TERMS),
        has_dish_hint=any(term in canonical for term in DISH_SHAPE_HINT_TERMS),
    )


@lru_cache(maxsize=512)
def _prepare_term_features(term: str) -> PreparedSearchText:
    normalized = _normalize_text(term)
    canonical = _canonicalize_synonyms(normalized)
    core = _strip_known_terms(canonical, QUANTITY_NOISE_TERMS) or canonical
    return PreparedSearchText(
        normalized=normalized,
        canonical=canonical,
        core=core,
        chars=frozenset(core),
        ngrams=frozenset(_build_ngrams(core)),
        modifiers=frozenset(_extract_modifiers(canonical)),
    )


def _canonicalize_synonyms(value: str) -> str:
    normalized = value
    for source, target in SYNONYM_REPLACEMENTS:
        normalized = normalized.replace(source, target)
    return normalized


def _strip_known_terms(value: str, terms: tuple[str, ...]) -> str:
    normalized = value
    for term in sorted(terms, key=len, reverse=True):
        normalized = normalized.replace(term, "")
    return normalized


def _build_ngrams(value: str) -> set[str]:
    if not value:
        return set()
    if len(value) < 2:
        return {value}

    ngrams: set[str] = set()
    for size in (2, 3, 4):
        if len(value) < size:
            continue
        for index in range(len(value) - size + 1):
            ngrams.add(value[index : index + size])
    return ngrams or {value}


def _extract_modifiers(value: str) -> set[str]:
    modifiers: set[str] = set()
    for label, keywords in MODIFIER_GROUPS.items():
        if any(keyword in value for keyword in keywords):
            modifiers.add(label)
    return modifiers


def _build_context(
    shortlisted: list[ScoredKnowledgeEntry],
    references: list[dict[str, str]],
    *,
    max_chars: int,
) -> str:
    lines = [
        "Chinese food knowledge context (high priority factual priors):",
        "- Use these entries as reference priors for Chinese foods when estimating/recommending.",
        "- If user-provided portion/cooking detail conflicts, follow user detail and explicitly note uncertainty.",
    ]
    for index, scored in enumerate(shortlisted, start=1):
        nutrition = scored.entry.nutrition_per_100g
        portion_hint = _format_portion_hint(scored.entry.portion_hints)
        notes = scored.entry.cooking_notes or "无"
        lines.append(
            (
                f"{index}. {scored.entry.canonical_name}: 每100g约"
                f"{nutrition['kcal']:.0f} kcal, 蛋白质 {nutrition['protein_g']:.1f} g, "
                f"碳水 {nutrition['carbs_g']:.1f} g, 脂肪 {nutrition['fat_g']:.1f} g; "
                f"常见份量={portion_hint}; 说明={notes}"
            )
        )
    if references:
        lines.append("References:")
        for index, ref in enumerate(references, start=1):
            lines.append(
                f"[{index}] {ref['food_name']} <- {ref['source_name']} ({ref['source_id']})"
            )

    context = "\n".join(lines)
    if len(context) > max_chars:
        return context[: max_chars - 3] + "..."
    return context


def _format_portion_hint(portion_hints: tuple[dict[str, Any], ...]) -> str:
    if not portion_hints:
        return "未标注"
    first = portion_hints[0]
    name = _optional_text(first.get("name")) or "常见份量"
    grams = first.get("grams")
    if isinstance(grams, (int, float)):
        return f"{name}约{int(grams)}g"
    return name


def _build_references(
    shortlisted: list[ScoredKnowledgeEntry],
    sources: dict[str, FoodKnowledgeSource],
) -> list[dict[str, str]]:
    references: list[dict[str, str]] = []
    for scored in shortlisted:
        source_id = scored.entry.source_ids[0] if scored.entry.source_ids else "unknown"
        source = sources.get(source_id)
        references.append(
            {
                "food_name": scored.entry.canonical_name,
                "source_id": source_id,
                "source_name": source.name if source else "Unknown source",
                "note": _truncate(scored.entry.cooking_notes, max_len=80),
                "updated_at": scored.entry.updated_at or (source.updated_at if source else ""),
            }
        )
    return references


def _normalize_ingredient_breakdown(raw: Any) -> tuple[dict[str, Any], ...]:
    if not isinstance(raw, list):
        return ()

    normalized: list[dict[str, Any]] = []
    for component in raw:
        if not isinstance(component, dict):
            continue
        name = _optional_text(component.get("name"))
        if not name:
            continue
        try:
            ratio = float(component.get("ratio"))
        except (TypeError, ValueError):
            continue
        if ratio <= 0:
            continue
        normalized.append(
            {
                "name": name,
                "ratio": ratio,
                "note": _optional_text(component.get("note")) or "",
            }
        )
    return tuple(normalized)


def _find_best_dish_for_breakdown(
    entries: tuple[FoodKnowledgeEntry, ...],
    *,
    normalized_query: str,
    normalized_primary_item: str,
) -> FoodKnowledgeEntry | None:
    ranked = _score_entries(entries, normalized_query or normalized_primary_item, scenario="estimate")
    for scored in ranked:
        entry = scored.entry
        if entry.category != "dish" or not entry.ingredient_breakdown:
            continue
        if not normalized_primary_item:
            return entry
        if _matches_primary_item(entry, normalized_primary_item):
            return entry
    return None


def _matches_primary_item(entry: FoodKnowledgeEntry, normalized_primary_item: str) -> bool:
    for term in entry.search_terms:
        normalized_term = _normalize_text(term)
        if not normalized_term:
            continue
        if normalized_term in normalized_primary_item or normalized_primary_item in normalized_term:
            return True
    return False


def _extract_float(value: str | None) -> float | None:
    if not value:
        return None
    match = FLOAT_RE.search(str(value))
    if not match:
        return None
    try:
        return float(match.group(1))
    except ValueError:
        return None


def _extract_grams(value: str | None) -> float | None:
    if not value:
        return None
    match = GRAM_RE.search(str(value))
    if not match:
        return None
    try:
        grams = float(match.group(1))
    except ValueError:
        return None
    return grams if grams > 0 else None


def _extract_default_portion_grams(entry: FoodKnowledgeEntry) -> float | None:
    if not entry.portion_hints:
        return None
    grams = entry.portion_hints[0].get("grams")
    if not isinstance(grams, (int, float)) or grams <= 0:
        return None
    return float(grams)


def _build_food_lookup(foods: tuple[FoodKnowledgeEntry, ...]) -> dict[str, FoodKnowledgeEntry]:
    lookup: dict[str, FoodKnowledgeEntry] = {}
    for entry in foods:
        for term in entry.search_terms:
            normalized_term = _normalize_text(term)
            if not normalized_term:
                continue
            lookup.setdefault(normalized_term, entry)
    return lookup


def _render_breakdown_components(
    *,
    target_dish: FoodKnowledgeEntry,
    total_calories_value: float,
    total_grams: float | None,
    food_lookup: dict[str, FoodKnowledgeEntry],
) -> list[dict[str, str]]:
    components = list(target_dish.ingredient_breakdown)
    ratio_sum = sum(float(component["ratio"]) for component in components)
    if ratio_sum <= 0:
        return []

    rendered: list[dict[str, str]] = []
    for component in components:
        normalized_ratio = float(component["ratio"]) / ratio_sum
        component_name = str(component["name"])
        component_kcal = max(total_calories_value * normalized_ratio, 1.0)
        component_grams = total_grams * normalized_ratio if total_grams is not None else None
        row: dict[str, str] = {
            "name": component_name,
            "portion": _format_component_portion(component_grams),
            "energy": f"{round(component_kcal):.0f} kcal",
        }

        nutrition_entry = food_lookup.get(_normalize_text(component_name))
        if nutrition_entry and component_grams is not None:
            nutrition = nutrition_entry.nutrition_per_100g
            protein = nutrition["protein_g"] * component_grams / 100.0
            carbs = nutrition["carbs_g"] * component_grams / 100.0
            fat = nutrition["fat_g"] * component_grams / 100.0
            row["protein"] = f"{protein:.1f} g"
            row["carbs"] = f"{carbs:.1f} g"
            row["fat"] = f"{fat:.1f} g"

        note = _optional_text(component.get("note"))
        if note:
            row["description"] = note
        rendered.append(row)

    return rendered


def _format_component_portion(component_grams: float | None) -> str:
    if component_grams is None:
        return "适量"
    return f"{round(component_grams):.0f} g"


def _truncate(value: str, *, max_len: int) -> str:
    stripped = value.strip()
    if len(stripped) <= max_len:
        return stripped
    return stripped[: max_len - 3] + "..."


def _normalize_text(value: str) -> str:
    lowered = value.lower().strip()
    compact = NON_TEXT_RE.sub("", lowered)
    return compact


def _optional_text(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()
