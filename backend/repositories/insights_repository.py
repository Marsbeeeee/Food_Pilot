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
    """Save or upsert an insights analysis record by user_id and cache_key."""
    close = conn is None
    if conn is None:
        conn = get_db_connection()

    try:
        selected_log_ids_json = json.dumps(selected_log_ids, ensure_ascii=False)
        result_json = result.model_dump_json(by_alias=True)

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
            ON CONFLICT(user_id, cache_key) DO UPDATE SET
                mode = excluded.mode,
                date_start = excluded.date_start,
                date_end = excluded.date_end,
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
    """List insights analysis records for a user, newest first."""
    close = conn is None
    if conn is None:
        conn = get_db_connection()

    try:
        rows = conn.execute(
            """
            SELECT cache_key, result_json
            FROM insights_analysis
            WHERE user_id = ?
            ORDER BY created_at DESC, id DESC
            LIMIT ?
            """,
            (user_id, limit),
        ).fetchall()

        result: list[dict[str, object]] = []
        for row in rows:
            try:
                data = InsightsAnalyzeData.model_validate(
                    json.loads(row["result_json"])
                )
                result.append({"cache_key": row["cache_key"], "data": data})
            except (json.JSONDecodeError, ValueError):
                continue
        return result
    finally:
        if close:
            conn.close()
