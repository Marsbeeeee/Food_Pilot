from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable
from unittest.mock import patch

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.food_knowledge import FoodKnowledgeConfig
from backend.services.food_knowledge import _load_dataset, retrieve_food_knowledge


@dataclass(frozen=True)
class RetrievalCase:
    query: str
    scenario: str
    expected_food: str


CASES = [
    RetrievalCase("一碗牛肉面大概多少热量", "estimate", "牛肉面"),
    RetrievalCase("早餐两个包子一杯豆浆", "estimate", "猪肉白菜包子"),
    RetrievalCase("奶茶有没有更健康的平替", "meal_recommendation", "珍珠奶茶"),
    RetrievalCase("麻辣烫和宫保鸡丁哪个更适合减脂", "meal_recommendation", "麻辣烫"),
]


def main() -> int:
    data_path = Path(__file__).resolve().parents[1] / "backend" / "data" / "chinese_food_kb_seed.json"
    if not data_path.exists():
        print(f"[FAIL] dataset missing: {data_path}")
        return 1

    dataset = _load_dataset(data_path)
    duplicate_names = _find_duplicates(food.canonical_name for food in dataset.foods)
    if duplicate_names:
        print(f"[FAIL] duplicate canonical names: {', '.join(sorted(duplicate_names))}")
        return 1
    if len(dataset.foods) < 15:
        print(f"[FAIL] dataset too small, expected >= 15 foods, got {len(dataset.foods)}")
        return 1

    print(f"[INFO] dataset version={dataset.version}, foods={len(dataset.foods)}, sources={len(dataset.sources)}")

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
            ok = result.has_hits and case.expected_food in matched_foods and bool(result.references)
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
                    f"expected contains: {case.expected_food}"
                )

    coverage = passed / len(CASES)
    print(f"[INFO] retrieval coverage={coverage:.0%} ({passed}/{len(CASES)})")
    if coverage < 0.75:
        print("[FAIL] retrieval coverage below threshold 75%")
        return 1

    print("[OK] food knowledge RAG validation passed")
    return 0


def _find_duplicates(values: Iterable[str]) -> set[str]:
    seen: set[str] = set()
    duplicates: set[str] = set()
    for value in values:
        if value in seen:
            duplicates.add(value)
            continue
        seen.add(value)
    return duplicates


if __name__ == "__main__":
    raise SystemExit(main())
