from datetime import date

from backend.schemas.insights import InsightsEntryBrief, NutritionAggregation
from backend.services.insights_service import (
    _build_insights_user_prompt,
    _build_week_trend_context,
)


def _build_aggregation() -> NutritionAggregation:
    return NutritionAggregation.model_validate(
        {
            "total_calories": 9800,
            "total_protein": 520,
            "total_carbs": 980,
            "total_fat": 360,
            "protein_ratio": 28,
            "carbs_ratio": 52,
            "fat_ratio": 20,
            "entry_count": 10,
        }
    )


def _build_entries() -> list[InsightsEntryBrief]:
    return [
        InsightsEntryBrief(
            id="1",
            name="Breakfast",
            calories="450",
            date="Mar 16",
            time="08:00 AM",
        ),
        InsightsEntryBrief(
            id="2",
            name="Dinner",
            calories="780",
            date="Mar 16",
            time="07:30 PM",
        ),
    ]


def _build_raw_entries() -> list[dict[str, object]]:
    return [
        {"meal_occurred_at": "2026-03-16 08:00:00", "total_calories": "450 kcal"},
        {"meal_occurred_at": "2026-03-16 19:30:00", "total_calories": "780 kcal"},
        {"meal_occurred_at": "2026-03-17 12:20:00", "total_calories": "980 kcal"},
        {"meal_occurred_at": "2026-03-18T12:20:00Z", "total_calories": "1100 kcal"},
        {"meal_occurred_at": "2026-03-21 18:40:00", "total_calories": "1650 kcal"},
    ]


def test_week_prompt_includes_trend_context_lines() -> None:
    prompt = _build_insights_user_prompt(
        _build_aggregation(),
        _build_entries(),
        mode="week",
        raw_entries=_build_raw_entries(),
        date_start=date(2026, 3, 16),
        date_end=date(2026, 3, 22),
    )

    assert "周趋势信息：" in prompt
    assert "按天热量：" in prompt
    assert "趋势判断：" in prompt
    assert "周期判断：" in prompt
    assert "优先总结趋势变化" in prompt


def test_day_prompt_does_not_include_week_trend_context() -> None:
    prompt = _build_insights_user_prompt(
        _build_aggregation(),
        _build_entries(),
        mode="day",
        raw_entries=_build_raw_entries(),
        date_start=date(2026, 3, 16),
        date_end=date(2026, 3, 16),
    )

    assert "周趋势信息：" not in prompt
    assert "优先总结趋势变化" not in prompt
    assert "请根据以上数据给出分析（summary、risks、actions）。" in prompt


def test_build_week_trend_context_ignores_out_of_range_entries() -> None:
    lines = _build_week_trend_context(
        [
            {"meal_occurred_at": "2026-03-15 20:00:00", "total_calories": "1500 kcal"},
            {"meal_occurred_at": "2026-03-16 08:00:00", "total_calories": "500 kcal"},
            {"meal_occurred_at": "2026-03-22 09:00:00", "total_calories": "700 kcal"},
            {"meal_occurred_at": "invalid", "total_calories": "1000 kcal"},
        ],
        date_start=date(2026, 3, 16),
        date_end=date(2026, 3, 22),
    )

    assert lines
    joined = "\n".join(lines)
    assert "03-15" not in joined
    assert "03-16" in joined
    assert "03-22" in joined
