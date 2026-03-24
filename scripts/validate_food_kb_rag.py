from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.food_knowledge import FoodKnowledgeConfig
from backend.services.food_knowledge import _load_dataset, retrieve_food_knowledge

MIN_FOOD_COUNT = 60
COVERAGE_THRESHOLD = 0.85
REQUIRED_NUTRITION_KEYS = ("kcal", "protein_g", "carbs_g", "fat_g")


@dataclass(frozen=True)
class RetrievalCase:
    query: str
    scenario: str
    expected_food: str


CASES = [
    RetrievalCase("一碗牛肉面大概多少热量", "estimate", "牛肉面"),
    RetrievalCase("早饭两个包子一杯豆浆热量高吗", "estimate", "猪肉白菜包子"),
    RetrievalCase("奶茶有没有更健康的平替", "meal_recommendation", "珍珠奶茶"),
    RetrievalCase("麻辣烫和宫保鸡丁哪个更适合减脂", "meal_recommendation", "麻辣烫"),
    RetrievalCase("兰州拉面热量高吗", "estimate", "兰州牛肉面"),
    RetrievalCase("三分糖波霸奶茶还能喝吗", "meal_recommendation", "低糖珍珠奶茶"),
    RetrievalCase("武汉热干面适合当早餐吗", "meal_recommendation", "热干面"),
    RetrievalCase("柳州螺蛳粉一碗大概多少卡", "estimate", "螺蛳粉"),
    RetrievalCase("一个肉夹馍大概多少热量", "estimate", "肉夹馍"),
    RetrievalCase("黄焖鸡米饭外卖怎么点更稳妥", "meal_recommendation", "黄焖鸡米饭"),
    RetrievalCase("鱼香肉丝盖饭是不是很油", "meal_recommendation", "鱼香肉丝"),
    RetrievalCase("生椰拿铁是不是比拿铁更高热量", "meal_recommendation", "生椰拿铁"),
    RetrievalCase("手打柠檬茶有什么更轻的点法", "meal_recommendation", "柠檬茶"),
    RetrievalCase("晚上吃酸菜鱼配米饭会不会太多", "meal_recommendation", "酸菜鱼"),
    RetrievalCase("豆花算不算低热量", "meal_recommendation", "豆腐脑"),
    RetrievalCase("老北京鸡肉卷大概多少卡", "estimate", "老北京鸡肉卷"),
    RetrievalCase("老北京炸酱面一碗多少热量", "estimate", "炸酱面"),
    RetrievalCase("清汤牛肉米线和酸辣粉哪个更适合减脂", "meal_recommendation", "牛肉米线"),
    RetrievalCase("煎饼果子加鸡蛋热量高吗", "estimate", "煎饼果子"),
    RetrievalCase("冰美式和杨枝甘露哪个更适合控糖", "meal_recommendation", "杨枝甘露"),
]


def main() -> int:
    data_path = Path(__file__).resolve().parents[1] / "backend" / "data" / "chinese_food_kb_seed.json"
    if not data_path.exists():
        print(f"[FAIL] dataset missing: {data_path}")
        return 1

    raw_payload = json.loads(data_path.read_text(encoding="utf-8"))
    dataset = _load_dataset(data_path)

    structural_failures = validate_dataset_payload(raw_payload, dataset)
    if structural_failures:
        for failure in structural_failures:
            print(f"[FAIL] {failure}")
        return 1

    print(
        "[INFO] "
        f"dataset version={dataset.version}, foods={len(dataset.foods)}, sources={len(dataset.sources)}, "
        f"coverage_target={COVERAGE_THRESHOLD:.0%}"
    )

    config = FoodKnowledgeConfig(
        enabled=True,
        data_path=data_path,
        top_k=3,
        min_score=1.0,
        max_context_chars=1200,
        only_chinese=True,
    )

    passed = 0
    with patch("backend.services.food_knowledge.get_food_knowledge_config", return_value=config):
        for case in CASES:
            result = retrieve_food_knowledge(case.query, scenario=case.scenario)
            matched_foods = [ref["food_name"] for ref in result.references]
            has_traceable_refs = bool(result.references) and all(
                _is_non_empty_text(ref.get("food_name"))
                and _is_non_empty_text(ref.get("source_id"))
                and _is_non_empty_text(ref.get("source_name"))
                and ref["source_id"] in dataset.sources
                for ref in result.references
            )
            ok = result.has_hits and case.expected_food in matched_foods and has_traceable_refs
            if ok:
                passed += 1
                print(
                    f"[PASS] {case.query} -> {matched_foods} "
                    f"(reason={result.reason}, hits={result.hit_count})"
                )
            else:
                print(
                    f"[FAIL] {case.query} -> {matched_foods} "
                    f"(reason={result.reason}, hits={result.hit_count}), "
                    f"expected contains: {case.expected_food}, traceable={has_traceable_refs}"
                )

    coverage = passed / len(CASES)
    print(f"[INFO] retrieval coverage={coverage:.0%} ({passed}/{len(CASES)})")
    if coverage < COVERAGE_THRESHOLD:
        print(f"[FAIL] retrieval coverage below threshold {COVERAGE_THRESHOLD:.0%}")
        return 1

    print("[OK] food knowledge RAG validation passed")
    return 0


def validate_dataset_payload(payload: dict[str, Any], dataset: Any) -> list[str]:
    failures: list[str] = []

    version = payload.get("version")
    if not _is_non_empty_text(version):
        failures.append("dataset version is required")
    elif not _is_valid_iso_date(version):
        failures.append(f"dataset version must be ISO date, got: {version}")

    raw_sources = payload.get("sources")
    if not isinstance(raw_sources, list) or not raw_sources:
        failures.append("sources must be a non-empty list")
    else:
        source_ids = []
        for index, source in enumerate(raw_sources):
            if not isinstance(source, dict):
                failures.append(f"sources[{index}] must be an object")
                continue
            source_id = source.get("id")
            source_name = source.get("name")
            source_type = source.get("type")
            updated_at = source.get("updated_at")
            if not _is_non_empty_text(source_id):
                failures.append(f"sources[{index}].id is required")
            if not _is_non_empty_text(source_name):
                failures.append(f"sources[{index}].name is required")
            if not _is_non_empty_text(source_type):
                failures.append(f"sources[{index}].type is required")
            if not _is_non_empty_text(updated_at):
                failures.append(f"sources[{index}].updated_at is required")
            elif not _is_valid_iso_date(updated_at):
                failures.append(f"sources[{index}].updated_at must be ISO date")
            if _is_non_empty_text(source_id):
                source_ids.append(str(source_id).strip())

        duplicate_source_ids = _find_duplicates(source_ids)
        if duplicate_source_ids:
            failures.append(f"duplicate source ids: {', '.join(sorted(duplicate_source_ids))}")

    raw_foods = payload.get("foods")
    if not isinstance(raw_foods, list):
        failures.append("foods must be a list")
        return failures

    if len(raw_foods) < MIN_FOOD_COUNT:
        failures.append(f"dataset too small, expected >= {MIN_FOOD_COUNT} foods, got {len(raw_foods)}")

    if len(raw_foods) != len(dataset.foods):
        failures.append(
            "loaded dataset size mismatch; at least one food entry could not be normalized cleanly"
        )

    duplicate_names = _find_duplicates(
        str(food.get("canonical_name", "")).strip() for food in raw_foods if isinstance(food, dict)
    )
    if duplicate_names:
        failures.append(f"duplicate canonical names: {', '.join(sorted(duplicate_names))}")

    duplicate_ids = _find_duplicates(
        str(food.get("id", "")).strip() for food in raw_foods if isinstance(food, dict)
    )
    if duplicate_ids:
        failures.append(f"duplicate food ids: {', '.join(sorted(duplicate_ids))}")

    known_source_ids = set(dataset.sources)
    missing_critical_fields = 0
    for index, food in enumerate(raw_foods):
        if not isinstance(food, dict):
            failures.append(f"foods[{index}] must be an object")
            missing_critical_fields += 1
            continue

        food_label = f"foods[{index}]"
        canonical_name = food.get("canonical_name")
        aliases = food.get("aliases")
        source_ids = food.get("source_ids")
        updated_at = food.get("updated_at")
        nutrition = food.get("nutrition_per_100g")

        if not _is_non_empty_text(canonical_name):
            failures.append(f"{food_label}.canonical_name is required")
            missing_critical_fields += 1
        if not isinstance(aliases, list) or not aliases or not all(_is_non_empty_text(alias) for alias in aliases):
            failures.append(f"{food_label}.aliases must be a non-empty list of strings")
            missing_critical_fields += 1
        elif len({str(alias).strip() for alias in aliases}) != len(aliases):
            failures.append(f"{food_label}.aliases must not contain duplicates")
        if not isinstance(source_ids, list) or not source_ids or not all(_is_non_empty_text(item) for item in source_ids):
            failures.append(f"{food_label}.source_ids must be a non-empty list of strings")
            missing_critical_fields += 1
        else:
            unknown_source_ids = sorted({str(item).strip() for item in source_ids if str(item).strip() not in known_source_ids})
            if unknown_source_ids:
                failures.append(
                    f"{food_label}.source_ids reference unknown sources: {', '.join(unknown_source_ids)}"
                )
        if not _is_non_empty_text(updated_at):
            failures.append(f"{food_label}.updated_at is required")
            missing_critical_fields += 1
        elif not _is_valid_iso_date(updated_at):
            failures.append(f"{food_label}.updated_at must be ISO date")
        if not isinstance(nutrition, dict):
            failures.append(f"{food_label}.nutrition_per_100g must be an object")
            missing_critical_fields += 1
        else:
            missing_keys = [key for key in REQUIRED_NUTRITION_KEYS if key not in nutrition]
            if missing_keys:
                failures.append(f"{food_label}.nutrition_per_100g missing keys: {', '.join(missing_keys)}")
                missing_critical_fields += 1
            for key in REQUIRED_NUTRITION_KEYS:
                value = nutrition.get(key)
                if not isinstance(value, (int, float)) or value < 0:
                    failures.append(f"{food_label}.nutrition_per_100g.{key} must be a non-negative number")
                    break

    if missing_critical_fields:
        failures.append(f"critical field missing count must be 0, got {missing_critical_fields}")

    change_summary = payload.get("change_summary")
    if not isinstance(change_summary, list) or not change_summary:
        failures.append("change_summary must be a non-empty list")
    else:
        matched_current_version = False
        for index, change in enumerate(change_summary):
            if not isinstance(change, dict):
                failures.append(f"change_summary[{index}] must be an object")
                continue
            summary_version = change.get("version")
            summary_text = change.get("summary")
            summary_updated_at = change.get("updated_at")
            added_food_count = change.get("added_food_count")
            if not _is_non_empty_text(summary_version):
                failures.append(f"change_summary[{index}].version is required")
            elif not _is_valid_iso_date(summary_version):
                failures.append(f"change_summary[{index}].version must be ISO date")
            if summary_version == version:
                matched_current_version = True
            if not _is_non_empty_text(summary_text):
                failures.append(f"change_summary[{index}].summary is required")
            if not _is_non_empty_text(summary_updated_at):
                failures.append(f"change_summary[{index}].updated_at is required")
            elif not _is_valid_iso_date(summary_updated_at):
                failures.append(f"change_summary[{index}].updated_at must be ISO date")
            if not isinstance(added_food_count, int) or added_food_count <= 0:
                failures.append(f"change_summary[{index}].added_food_count must be a positive integer")
        if version and not matched_current_version:
            failures.append("change_summary must contain an entry for the current dataset version")

    return failures


def _find_duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if not value:
            continue
        if value in seen:
            duplicates.add(value)
            continue
        seen.add(value)
    return duplicates


def _is_non_empty_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _is_valid_iso_date(value: Any) -> bool:
    if not _is_non_empty_text(value):
        return False
    try:
        date.fromisoformat(str(value).strip())
    except ValueError:
        return False
    return True


if __name__ == "__main__":
    raise SystemExit(main())
