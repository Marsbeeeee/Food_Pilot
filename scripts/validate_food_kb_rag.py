from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from datetime import date
from pathlib import Path
from typing import Any, Iterable

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from backend.config.food_knowledge import FoodKnowledgeConfig
from backend.services.food_knowledge import (
    CHINESE_CHAR_RE,
    _build_references,
    _load_dataset,
    _normalize_text,
    _score_entries,
)

MIN_FOOD_COUNT = 60
REQUIRED_NUTRITION_KEYS = ("kcal", "protein_g", "carbs_g", "fat_g")
RELATIVE_IMPROVEMENT_THRESHOLD = 0.10
EPSILON = 1e-9


@dataclass(frozen=True)
class RetrievalCase:
    case_id: str
    query: str
    scenario: str
    expected_hit: bool
    expected_top1: str | None
    expected_any: tuple[str, ...]


@dataclass(frozen=True)
class CaseOutcome:
    case: RetrievalCase
    scorer: str
    reason: str
    hit_count: int
    matched_foods: tuple[str, ...]
    top1_ok: bool
    recall_hits: int
    recall_total: int
    citation_complete: bool
    expected_hit_ok: bool


@dataclass(frozen=True)
class MetricSummary:
    case_count: int
    positive_case_count: int
    negative_case_count: int
    hit_rate: float
    top1_accuracy: float
    topk_recall: float
    citation_completeness_rate: float
    no_hit_rate: float
    negative_pass_rate: float


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate food KB retrieval quality and regression baseline.")
    parser.add_argument(
        "--update-baseline",
        action="store_true",
        help="Write the current metrics snapshot into the baseline JSON file.",
    )
    args = parser.parse_args()

    data_path = PROJECT_ROOT / "backend" / "data" / "chinese_food_kb_seed.json"
    eval_case_path = PROJECT_ROOT / "backend" / "data" / "food_kb_eval_cases.json"
    baseline_path = PROJECT_ROOT / "backend" / "data" / "food_kb_quality_baseline.json"

    if not data_path.exists():
        print(f"[FAIL] dataset missing: {data_path}")
        return 1
    if not eval_case_path.exists():
        print(f"[FAIL] eval cases missing: {eval_case_path}")
        return 1

    raw_payload = json.loads(data_path.read_text(encoding="utf-8"))
    dataset = _load_dataset(data_path)
    structural_failures = validate_dataset_payload(raw_payload, dataset)
    if structural_failures:
        for failure in structural_failures:
            print(f"[FAIL] {failure}")
        return 1

    cases = load_eval_cases(eval_case_path)
    print(
        "[INFO] "
        f"dataset version={dataset.version}, foods={len(dataset.foods)}, sources={len(dataset.sources)}, "
        f"eval_cases={len(cases)}"
    )

    config = FoodKnowledgeConfig(
        enabled=True,
        data_path=data_path,
        top_k=3,
        min_score=1.35,
        max_context_chars=1200,
        only_chinese=True,
    )

    legacy_outcomes = evaluate_cases(dataset, cases, config=config, scorer="legacy")
    enhanced_outcomes = evaluate_cases(dataset, cases, config=config, scorer="enhanced")
    legacy_metrics = summarize_metrics(legacy_outcomes)
    enhanced_metrics = summarize_metrics(enhanced_outcomes)

    print_metric_summary("legacy", legacy_metrics)
    print_metric_summary("enhanced", enhanced_metrics)
    print_case_deltas(legacy_outcomes, enhanced_outcomes)

    baseline_payload = build_baseline_payload(
        dataset_version=dataset.version,
        case_count=len(cases),
        legacy_metrics=legacy_metrics,
        enhanced_metrics=enhanced_metrics,
    )

    failures = validate_metric_thresholds(legacy_metrics, enhanced_metrics)
    if baseline_path.exists():
        failures.extend(validate_against_baseline(baseline_path, enhanced_metrics))

    if failures:
        for failure in failures:
            print(f"[FAIL] {failure}")
        return 1

    if args.update_baseline:
        baseline_path.write_text(
            json.dumps(baseline_payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )
        print(f"[OK] baseline updated: {baseline_path}")
    else:
        print("[OK] food knowledge retrieval validation passed")
    return 0


def load_eval_cases(path: Path) -> list[RetrievalCase]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, list) or not payload:
        raise ValueError("eval cases must be a non-empty list")

    cases: list[RetrievalCase] = []
    for index, raw_case in enumerate(payload):
        if not isinstance(raw_case, dict):
            raise ValueError(f"eval case {index} must be an object")

        case_id = str(raw_case.get("id", "")).strip()
        query = str(raw_case.get("query", "")).strip()
        scenario = str(raw_case.get("scenario", "")).strip()
        expected_hit = bool(raw_case.get("expected_hit", True))
        expected_top1 = _optional_non_empty_text(raw_case.get("expected_top1"))
        expected_any = tuple(
            item
            for item in (
                _optional_non_empty_text(value)
                for value in raw_case.get("expected_any", [])
                if isinstance(value, str) or value is not None
            )
            if item
        )

        if not case_id:
            raise ValueError(f"eval case {index} is missing id")
        if not query:
            raise ValueError(f"eval case {case_id} is missing query")
        if scenario not in {"estimate", "meal_recommendation", "text"}:
            raise ValueError(f"eval case {case_id} has unsupported scenario: {scenario}")
        if expected_hit and not expected_any and expected_top1 is None:
            raise ValueError(f"eval case {case_id} must declare expected_top1 or expected_any")
        if expected_top1 and expected_any and expected_top1 not in expected_any:
            expected_any = (expected_top1, *expected_any)

        cases.append(
            RetrievalCase(
                case_id=case_id,
                query=query,
                scenario=scenario,
                expected_hit=expected_hit,
                expected_top1=expected_top1,
                expected_any=expected_any,
            )
        )
    return cases


def evaluate_cases(
    dataset: Any,
    cases: list[RetrievalCase],
    *,
    config: FoodKnowledgeConfig,
    scorer: str,
) -> list[CaseOutcome]:
    return [
        evaluate_case(dataset, case, config=config, scorer=scorer)
        for case in cases
    ]


def evaluate_case(
    dataset: Any,
    case: RetrievalCase,
    *,
    config: FoodKnowledgeConfig,
    scorer: str,
) -> CaseOutcome:
    normalized_query = _normalize_text(case.query)
    if not normalized_query:
        return build_case_outcome(case, scorer, reason="empty_query", references=[])
    if config.only_chinese and not CHINESE_CHAR_RE.search(case.query):
        return build_case_outcome(case, scorer, reason="non_chinese_query", references=[])

    ranked = _score_entries(dataset.foods, normalized_query, scenario=case.scenario, scorer=scorer)
    shortlisted = [item for item in ranked if item.score >= config.min_score][: config.top_k]
    references = _build_references(shortlisted, dataset.sources) if shortlisted else []
    reason = "ok" if shortlisted else "no_match"
    return build_case_outcome(case, scorer, reason=reason, references=references)


def build_case_outcome(
    case: RetrievalCase,
    scorer: str,
    *,
    reason: str,
    references: list[dict[str, str]],
) -> CaseOutcome:
    matched_foods = tuple(ref["food_name"] for ref in references)
    expected_items = case.expected_any
    recall_hits = len([item for item in expected_items if item in matched_foods]) if case.expected_hit else 0
    recall_total = len(expected_items) if case.expected_hit else 0
    top1_ok = (not case.expected_hit) or (
        case.expected_top1 is None
        or (bool(matched_foods) and matched_foods[0] == case.expected_top1)
    )
    citation_complete = bool(references) and all(
        _optional_non_empty_text(ref.get("food_name"))
        and _optional_non_empty_text(ref.get("source_id"))
        and _optional_non_empty_text(ref.get("source_name"))
        for ref in references
    )
    expected_hit_ok = bool(references) if case.expected_hit else not bool(references)
    return CaseOutcome(
        case=case,
        scorer=scorer,
        reason=reason,
        hit_count=len(references),
        matched_foods=matched_foods,
        top1_ok=top1_ok,
        recall_hits=recall_hits,
        recall_total=recall_total,
        citation_complete=citation_complete,
        expected_hit_ok=expected_hit_ok,
    )


def summarize_metrics(outcomes: list[CaseOutcome]) -> MetricSummary:
    positive_cases = [outcome for outcome in outcomes if outcome.case.expected_hit]
    negative_cases = [outcome for outcome in outcomes if not outcome.case.expected_hit]
    positive_hits = sum(1 for outcome in positive_cases if outcome.hit_count > 0)
    top1_total = sum(1 for outcome in positive_cases if outcome.case.expected_top1 is not None)
    top1_hits = sum(1 for outcome in positive_cases if outcome.case.expected_top1 is not None and outcome.top1_ok)
    recall_total = sum(outcome.recall_total for outcome in positive_cases)
    recall_hits = sum(outcome.recall_hits for outcome in positive_cases)
    hit_outcomes = [outcome for outcome in outcomes if outcome.hit_count > 0]
    citation_hits = sum(1 for outcome in hit_outcomes if outcome.citation_complete)
    no_hit_count = sum(1 for outcome in outcomes if outcome.hit_count == 0)
    negative_passes = sum(1 for outcome in negative_cases if outcome.expected_hit_ok)

    return MetricSummary(
        case_count=len(outcomes),
        positive_case_count=len(positive_cases),
        negative_case_count=len(negative_cases),
        hit_rate=(positive_hits / len(positive_cases)) if positive_cases else 1.0,
        top1_accuracy=(top1_hits / top1_total) if top1_total else 1.0,
        topk_recall=(recall_hits / recall_total) if recall_total else 1.0,
        citation_completeness_rate=(citation_hits / len(hit_outcomes)) if hit_outcomes else 1.0,
        no_hit_rate=no_hit_count / len(outcomes) if outcomes else 0.0,
        negative_pass_rate=(negative_passes / len(negative_cases)) if negative_cases else 1.0,
    )


def validate_metric_thresholds(
    legacy: MetricSummary,
    enhanced: MetricSummary,
) -> list[str]:
    failures: list[str] = []
    top1_improvement = relative_improvement(legacy.top1_accuracy, enhanced.top1_accuracy)
    recall_improvement = relative_improvement(legacy.topk_recall, enhanced.topk_recall)

    if top1_improvement + EPSILON < RELATIVE_IMPROVEMENT_THRESHOLD:
        failures.append(
            "Top-1 accuracy relative improvement is below threshold: "
            f"{top1_improvement:.1%} < {RELATIVE_IMPROVEMENT_THRESHOLD:.0%}"
        )
    if recall_improvement + EPSILON < RELATIVE_IMPROVEMENT_THRESHOLD:
        failures.append(
            "Top-K recall relative improvement is below threshold: "
            f"{recall_improvement:.1%} < {RELATIVE_IMPROVEMENT_THRESHOLD:.0%}"
        )
    if enhanced.citation_completeness_rate + EPSILON < 1.0:
        failures.append("citation completeness rate must remain 100% on hit samples")
    if enhanced.no_hit_rate > legacy.no_hit_rate + EPSILON:
        failures.append(
            f"no-hit rate regressed: enhanced={enhanced.no_hit_rate:.1%}, legacy={legacy.no_hit_rate:.1%}"
        )
    if enhanced.negative_pass_rate + EPSILON < 1.0:
        failures.append("negative eval cases must keep 100% no-hit pass rate")
    return failures


def validate_against_baseline(path: Path, current: MetricSummary) -> list[str]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    metrics = payload.get("metrics", {})
    baseline = metrics.get("enhanced", {})
    failures: list[str] = []

    for field in ("hit_rate", "top1_accuracy", "topk_recall", "citation_completeness_rate", "negative_pass_rate"):
        baseline_value = float(baseline.get(field, 0.0))
        current_value = float(getattr(current, field))
        if current_value + EPSILON < baseline_value:
            failures.append(
                f"{field} regressed from baseline: current={current_value:.1%}, baseline={baseline_value:.1%}"
            )

    baseline_no_hit_rate = float(baseline.get("no_hit_rate", 1.0))
    if current.no_hit_rate > baseline_no_hit_rate + EPSILON:
        failures.append(
            f"no_hit_rate regressed from baseline: current={current.no_hit_rate:.1%}, baseline={baseline_no_hit_rate:.1%}"
        )
    return failures


def build_baseline_payload(
    *,
    dataset_version: str,
    case_count: int,
    legacy_metrics: MetricSummary,
    enhanced_metrics: MetricSummary,
) -> dict[str, Any]:
    return {
        "generated_at": date.today().isoformat(),
        "dataset_version": dataset_version,
        "case_count": case_count,
        "thresholds": {
            "top1_relative_improvement_min": RELATIVE_IMPROVEMENT_THRESHOLD,
            "topk_recall_relative_improvement_min": RELATIVE_IMPROVEMENT_THRESHOLD,
            "citation_completeness_rate_min": 1.0,
            "negative_pass_rate_min": 1.0,
        },
        "metrics": {
            "legacy": asdict(legacy_metrics),
            "enhanced": asdict(enhanced_metrics),
        },
    }


def print_metric_summary(label: str, metrics: MetricSummary) -> None:
    print(
        f"[INFO] {label}: "
        f"hit_rate={metrics.hit_rate:.1%}, "
        f"top1_accuracy={metrics.top1_accuracy:.1%}, "
        f"topk_recall={metrics.topk_recall:.1%}, "
        f"citation_completeness={metrics.citation_completeness_rate:.1%}, "
        f"no_hit_rate={metrics.no_hit_rate:.1%}, "
        f"negative_pass_rate={metrics.negative_pass_rate:.1%}"
    )


def print_case_deltas(legacy_outcomes: list[CaseOutcome], enhanced_outcomes: list[CaseOutcome]) -> None:
    for legacy, enhanced in zip(legacy_outcomes, enhanced_outcomes):
        if legacy.case.case_id != enhanced.case.case_id:
            continue
        if legacy.matched_foods == enhanced.matched_foods:
            continue
        print(
            f"[CASE] {legacy.case.case_id}: "
            f"legacy={list(legacy.matched_foods)} -> enhanced={list(enhanced.matched_foods)}"
        )


def relative_improvement(baseline: float, current: float) -> float:
    if baseline <= EPSILON:
        return 1.0 if current > baseline else 0.0
    return (current - baseline) / baseline


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
            unknown_source_ids = sorted(
                {str(item).strip() for item in source_ids if str(item).strip() not in known_source_ids}
            )
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


def _optional_non_empty_text(value: Any) -> str | None:
    if value is None:
        return None
    normalized = str(value).strip()
    return normalized or None


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
