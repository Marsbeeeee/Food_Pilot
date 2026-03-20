"""Repository for insights analysis history persistence."""

import json
import sqlite3
from datetime import date

from backend.database.connection import get_db_connection
from backend.schemas.insights import InsightsAnalyzeData


def save_insights_analysis(
    user_id: int,
    *,
    cache_key: str,
    mode: str,
    date_start: date,
    date_end: date,
    selected_log_ids: list[int],
    result: InsightsAnalyzeData,
    conn: sqlite3.Connection | None = None,
) -> None:
    """Save or upsert an insights analysis record by business date range key."""
    close = conn is None
    if conn is None:
        conn = get_db_connection()

    try:
        selected_log_ids_json = json.dumps(selected_log_ids, ensure_ascii=False)
        result_json = result.model_dump_json()

        conn.execute(
            """
            INSERT INTO insights_analysis (
                user_id,
                cache_key,
                mode,
                date_start,
                date_end,
                selected_log_ids_json,
                result_json
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(user_id, mode, date_start, date_end) DO UPDATE SET
                cache_key = excluded.cache_key,
                selected_log_ids_json = excluded.selected_log_ids_json,
                result_json = excluded.result_json,
                created_at = CURRENT_TIMESTAMP
            """,
            (
                user_id,
                cache_key,
                mode,
                str(date_start),
                str(date_end),
                selected_log_ids_json,
                result_json,
            ),
        )
        if close:
            conn.commit()
    finally:
        if close:
            conn.close()


def list_insights_analysis_by_user(
    user_id: int,
    *,
    limit: int = 100,
    conn: sqlite3.Connection | None = None,
) -> list[dict[str, object]]:
    """List latest insights analysis records by range for a user, newest first."""
    close = conn is None
    if conn is None:
        conn = get_db_connection()

    try:
        rows = conn.execute(
            """
            SELECT
                current.cache_key,
                current.mode,
                current.date_start,
                current.date_end,
                current.result_json
            FROM insights_analysis AS current
            WHERE current.user_id = ?
            AND NOT EXISTS (
                SELECT 1
                FROM insights_analysis AS newer
                WHERE newer.user_id = current.user_id
                AND newer.mode = current.mode
                AND newer.date_start = current.date_start
                AND newer.date_end = current.date_end
                AND (
                    newer.created_at > current.created_at
                    OR (
                        newer.created_at = current.created_at
                        AND newer.id > current.id
                    )
                )
            )
            ORDER BY current.created_at DESC, current.id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()

        result: list[dict[str, object]] = []
        for row in rows:
            try:
                payload = json.loads(row["result_json"])
                try:
                    data = InsightsAnalyzeData.model_validate(payload)
                except ValueError:
                    data = InsightsAnalyzeData.model_validate(
                        _normalize_legacy_insights_result_payload(payload)
                    )
                result.append(
                    {
                        "cache_key": row["cache_key"],
                        "mode": row["mode"],
                        "date_start": row["date_start"],
                        "date_end": row["date_end"],
                        "data": data,
                    }
                )
            except (json.JSONDecodeError, ValueError):
                continue
        return result
    finally:
        if close:
            conn.close()


def _normalize_legacy_insights_result_payload(payload: object) -> object:
    """Normalize historical camelCase serialization into current schema keys."""
    if not isinstance(payload, dict):
        return payload

    normalized = dict(payload)
    aggregation = payload.get("aggregation")
    if isinstance(aggregation, dict):
        normalized["aggregation"] = {
            "total_calories": aggregation.get("total_calories", aggregation.get("totalCalories")),
            "total_protein": aggregation.get("total_protein", aggregation.get("totalProtein")),
            "total_carbs": aggregation.get("total_carbs", aggregation.get("totalCarbs")),
            "total_fat": aggregation.get("total_fat", aggregation.get("totalFat")),
            "protein_ratio": aggregation.get("protein_ratio", aggregation.get("proteinRatio")),
            "carbs_ratio": aggregation.get("carbs_ratio", aggregation.get("carbsRatio")),
            "fat_ratio": aggregation.get("fat_ratio", aggregation.get("fatRatio")),
            "entry_count": aggregation.get("entry_count", aggregation.get("entryCount")),
        }
    return normalized
