import json
import re
import time
from datetime import date
from pathlib import Path
from typing import Any
from urllib import error, request

from backend.config.estimate import get_estimate_ai_config
from backend.services.ai_client import call_ai
from backend.database.connection import get_db_connection
from backend.repositories.food_log_repository import (
    get_food_log_by_id as get_food_log_by_id_record,
    list_food_logs_by_user as list_food_logs_by_user_record,
)
from backend.schemas.food_log import parse_food_log_items, serialize_food_log_entry
from backend.schemas.insights import (
    AIInsights,
    InsightsAnalyzeData,
    InsightsEntryBrief,
    NutritionAggregation,
)
from backend.services.insights_contract import (
    INSIGHTS_RESPONSE_SCHEMA,
    INSIGHTS_SYSTEM_PROMPT,
)

# #region agent log
def _dbg_log(msg: str, data: dict, hyp: str = "") -> None:
    try:
        p = Path(__file__).resolve().parents[2] / "debug-9096da.log"
        entry = {"sessionId": "9096da", "location": "insights_service.py", "message": msg, "data": data, "timestamp": int(time.time() * 1000)}
        if hyp:
            entry["hypothesisId"] = hyp
        p.open("a", encoding="utf-8").write(json.dumps(entry, ensure_ascii=False) + "\n")
    except Exception:
        pass
# #endregion


class InsightsServiceError(Exception):
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


class EmptyLogsError(InsightsServiceError):
    def __init__(self) -> None:
        super().__init__(
            code="INSIGHTS_NO_DATA",
            status_code=404,
            message="No food log entries found for the given criteria",
            user_message="所选范围内没有饮食记录，无法生成分析。",
            retryable=False,
        )


class IncompleteDataError(InsightsServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(
            code="INSIGHTS_DATA_INCOMPLETE",
            status_code=422,
            message=message,
            user_message="部分饮食记录数据不完整，分析结果可能不准确。",
            retryable=False,
        )


class AIConfigMissingError(InsightsServiceError):
    def __init__(self) -> None:
        super().__init__(
            code="AI_CONFIG_MISSING",
            status_code=503,
            message="GEMINI_API_KEY is missing",
            user_message="分析服务暂未配置，请稍后再试。",
            retryable=False,
        )


class AIUpstreamError(InsightsServiceError):
    def __init__(
        self,
        message: str,
        *,
        retryable: bool,
        user_message: str | None = None,
    ) -> None:
        super().__init__(
            code="AI_UPSTREAM_ERROR",
            status_code=503,
            message=message,
            user_message=user_message or "AI 分析服务暂时不可用，请稍后重试。",
            retryable=retryable,
        )


class AIResponseInvalidError(InsightsServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(
            code="AI_RESPONSE_INVALID",
            status_code=502,
            message=message,
            user_message="AI 分析服务返回结果异常，请稍后重试。",
            retryable=True,
        )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def analyze_insights(
    user_id: int,
    *,
    mode: str,
    selected_log_ids: list[int] | None,
    date_start: date,
    date_end: date,
) -> InsightsAnalyzeData:
    entries = _fetch_food_log_entries(
        user_id,
        selected_log_ids=selected_log_ids,
        date_start=date_start,
        date_end=date_end,
    )

    if not entries:
        raise EmptyLogsError()

    aggregation = _aggregate_nutrition(entries)
    entry_briefs = _build_entry_briefs(entries)
    ai_insights = _generate_ai_insights(aggregation, entry_briefs, mode=mode)

    return InsightsAnalyzeData(
        aggregation=aggregation,
        entries=entry_briefs,
        ai=ai_insights,
    )


# ---------------------------------------------------------------------------
# Data fetching
# ---------------------------------------------------------------------------


def _fetch_food_log_entries(
    user_id: int,
    *,
    selected_log_ids: list[int] | None,
    date_start: date,
    date_end: date,
) -> list[dict[str, object]]:
    conn = get_db_connection()
    try:
        if selected_log_ids:
            entries = []
            for log_id in selected_log_ids:
                entry = get_food_log_by_id_record(conn, log_id, user_id)
                if entry is not None:
                    entries.append(entry)
            return entries

        return list_food_logs_by_user_record(
            conn,
            user_id,
            date_from=date_start,
            date_to=date_end,
        )
    finally:
        conn.close()


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def _extract_grams(value: str | None) -> float:
    if not value:
        return 0.0
    match = re.search(r"(\d+(?:\.\d+)?)", str(value).replace(",", ""))
    if match is None:
        return 0.0
    parsed = float(match.group(1))
    return parsed if parsed == parsed else 0.0


def _extract_calories(value: object) -> float:
    if not isinstance(value, str):
        return 0.0
    match = re.search(r"(\d+(?:\.\d+)?)", value.replace(",", ""))
    if match is None:
        return 0.0
    return float(match.group(1))


def _aggregate_nutrition(entries: list[dict[str, object]]) -> NutritionAggregation:
    total_calories = 0.0
    total_protein = 0.0
    total_carbs = 0.0
    total_fat = 0.0
    incomplete_count = 0

    for entry in entries:
        total_calories += _extract_calories(entry.get("total_calories"))

        ingredients_json = entry.get("ingredients_json")
        if not isinstance(ingredients_json, str) or not ingredients_json.strip():
            incomplete_count += 1
            continue

        try:
            items = parse_food_log_items(ingredients_json)
        except (ValueError, json.JSONDecodeError):
            incomplete_count += 1
            continue

        for item in items:
            total_protein += _extract_grams(item.protein)
            total_carbs += _extract_grams(item.carbs)
            total_fat += _extract_grams(item.fat)

    macro_total = total_protein + total_carbs + total_fat
    protein_ratio = round(total_protein / macro_total * 100, 1) if macro_total > 0 else 0.0
    carbs_ratio = round(total_carbs / macro_total * 100, 1) if macro_total > 0 else 0.0
    fat_ratio = round(total_fat / macro_total * 100, 1) if macro_total > 0 else 0.0

    if incomplete_count > 0 and incomplete_count == len(entries):
        raise IncompleteDataError(
            f"All {len(entries)} food log entries have incomplete nutrition data"
        )

    return NutritionAggregation(
        total_calories=round(total_calories, 1),
        total_protein=round(total_protein, 1),
        total_carbs=round(total_carbs, 1),
        total_fat=round(total_fat, 1),
        protein_ratio=protein_ratio,
        carbs_ratio=carbs_ratio,
        fat_ratio=fat_ratio,
        entry_count=len(entries),
    )


# ---------------------------------------------------------------------------
# Entry brief builder
# ---------------------------------------------------------------------------


def _build_entry_briefs(entries: list[dict[str, object]]) -> list[InsightsEntryBrief]:
    briefs: list[InsightsEntryBrief] = []
    for entry in entries:
        serialized = serialize_food_log_entry(entry)
        briefs.append(
            InsightsEntryBrief(
                id=serialized.id,
                name=serialized.name,
                calories=serialized.calories,
                date=serialized.date,
                time=serialized.time,
            )
        )
    return briefs


# ---------------------------------------------------------------------------
# AI insights generation
# ---------------------------------------------------------------------------


def _generate_ai_insights(
    aggregation: NutritionAggregation,
    entries: list[InsightsEntryBrief],
    *,
    mode: str,
) -> AIInsights:
    config = get_estimate_ai_config()
    # #region agent log
    _dbg_log("AI config before call", {"api_key_present": bool(config.api_key), "model": config.model, "timeout": config.timeout_seconds}, "H1")
    # #endregion
    if not config.api_key:
        raise AIConfigMissingError()

    user_prompt = _build_insights_user_prompt(aggregation, entries, mode=mode)
    raw = _call_ai_for_insights(config, user_prompt)

    summary = str(raw.get("summary") or "").strip()
    risks_raw = raw.get("risks")
    actions_raw = raw.get("actions")

    if not summary:
        raise AIResponseInvalidError("AI response is missing summary")

    risks = _coerce_string_list(risks_raw)
    actions = _coerce_string_list(actions_raw)

    if not actions:
        raise AIResponseInvalidError("AI response is missing actions")

    return AIInsights(summary=summary, risks=risks, actions=actions)


def _build_insights_user_prompt(
    aggregation: NutritionAggregation,
    entries: list[InsightsEntryBrief],
    *,
    mode: str,
) -> str:
    mode_label = "单日" if mode == "day" else "一周"

    lines = [
        f"以下是用户{mode_label}的饮食记录汇总：",
        "",
        f"- 总热量: {aggregation.total_calories} kcal",
        f"- 总蛋白质: {aggregation.total_protein} g",
        f"- 总碳水化合物: {aggregation.total_carbs} g",
        f"- 总脂肪: {aggregation.total_fat} g",
        f"- 蛋白质占比: {aggregation.protein_ratio}%",
        f"- 碳水占比: {aggregation.carbs_ratio}%",
        f"- 脂肪占比: {aggregation.fat_ratio}%",
        f"- 记录条目数: {aggregation.entry_count}",
        "",
        "具体条目：",
    ]

    for entry in entries[:30]:
        lines.append(f"  · {entry.name}（{entry.calories} kcal，{entry.date} {entry.time}）")

    if len(entries) > 30:
        lines.append(f"  …… 以及另外 {len(entries) - 30} 条记录")

    lines.append("")
    lines.append("请根据以上数据给出分析（summary、risks、actions）。")

    return "\n".join(lines)


def _call_ai_for_insights(config: Any, user_prompt: str) -> dict[str, Any]:
    # #region agent log
    _dbg_log("AI request start", {"model": config.model}, "H5")
    # #endregion
    try:
        return call_ai(
            config,
            INSIGHTS_SYSTEM_PROMPT,
            user_prompt,
            response_schema=INSIGHTS_RESPONSE_SCHEMA,
        )
    except error.HTTPError as exc:
        body = exc.read()
        detail = ""
        try:
            detail = body.decode("utf-8", errors="replace")[:500]
        except Exception:
            pass
        # #region agent log
        _dbg_log("AI HTTPError", {"code": exc.code, "detail_snippet": detail[:200]}, "H2" if exc.code in (401, 403) else "H3")
        # #endregion
        if exc.code in {401, 403}:
            raise AIUpstreamError(
                f"AI provider authentication failed. {detail}",
                retryable=False,
            ) from exc
        if exc.code == 429:
            raise AIUpstreamError(
                f"AI provider request failed ({exc.code}). {detail}",
                retryable=True,
                user_message="API 配额已用完，请检查计划与账单，或稍后重试。",
            ) from exc
        raise AIUpstreamError(
            f"AI provider request failed ({exc.code}). {detail}",
            retryable=exc.code >= 500,
        ) from exc
    except error.URLError as exc:
        # #region agent log
        _dbg_log("AI URLError", {"reason": str(getattr(exc, "reason", exc))}, "H4")
        # #endregion
        raise AIUpstreamError(
            "AI provider is temporarily unavailable.",
            retryable=True,
        ) from exc
    except json.JSONDecodeError as exc:
        raise AIResponseInvalidError(
            "AI provider did not return valid JSON"
        ) from exc


def _coerce_string_list(value: Any) -> list[str]:
    if not isinstance(value, list):
        return []
    return [str(item).strip() for item in value if str(item).strip()]
