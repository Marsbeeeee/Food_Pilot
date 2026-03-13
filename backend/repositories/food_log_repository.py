import json
import sqlite3
from collections.abc import Sequence


FOOD_LOG_SELECT_COLUMNS = """
    id,
    user_id,
    session_id,
    source_message_id,
    meal_description,
    logged_at,
    result_title,
    result_confidence,
    result_description,
    total_calories,
    ingredients_json,
    source_type,
    assistant_suggestion,
    created_at,
    updated_at
"""


def create_food_log(
    conn: sqlite3.Connection,
    user_id: int,
    *,
    source_type: str,
    meal_description: str,
    result_title: str,
    result_description: str,
    total_calories: str,
    ingredients: str | Sequence[dict[str, object]],
    session_id: int | None = None,
    source_message_id: int | None = None,
    result_confidence: str | None = None,
    assistant_suggestion: str | None = None,
    logged_at: str | None = None,
    created_at: str | None = None,
    auto_commit: bool = True,
) -> dict[str, object]:
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO food_logs (
            user_id,
            session_id,
            source_message_id,
            meal_description,
            logged_at,
            result_title,
            result_confidence,
            result_description,
            total_calories,
            ingredients_json,
            source_type,
            assistant_suggestion,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), ?, ?, ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), COALESCE(?, CURRENT_TIMESTAMP))
        """,
        (
            user_id,
            session_id,
            source_message_id,
            meal_description,
            logged_at,
            result_title,
            result_confidence,
            result_description,
            total_calories,
            _serialize_ingredients(ingredients),
            source_type,
            assistant_suggestion,
            created_at,
            created_at,
        ),
    )
    if auto_commit:
        conn.commit()
    food_log = get_food_log_by_id(conn, cursor.lastrowid, user_id)
    if food_log is None:
        raise LookupError("food log not found after insert")
    return food_log


def get_food_log_by_id(
    conn: sqlite3.Connection,
    food_log_id: int,
    user_id: int,
) -> dict[str, object] | None:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            {FOOD_LOG_SELECT_COLUMNS}
        FROM food_logs
        WHERE id = ? AND user_id = ?
        """,
        (food_log_id, user_id),
    )
    row = cursor.fetchone()
    return _row_to_food_log(row)


def list_food_logs_by_user(
    conn: sqlite3.Connection,
    user_id: int,
    *,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict[str, object]]:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            {FOOD_LOG_SELECT_COLUMNS}
        FROM food_logs
        WHERE user_id = ?
        ORDER BY logged_at DESC, id DESC
        LIMIT COALESCE(?, -1) OFFSET ?
        """,
        (user_id, limit, offset),
    )
    return [_row_to_food_log(row) for row in cursor.fetchall()]


def list_food_logs_by_session(
    conn: sqlite3.Connection,
    user_id: int,
    session_id: int,
    *,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict[str, object]]:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            {FOOD_LOG_SELECT_COLUMNS}
        FROM food_logs
        WHERE user_id = ? AND session_id = ?
        ORDER BY logged_at DESC, id DESC
        LIMIT COALESCE(?, -1) OFFSET ?
        """,
        (user_id, session_id, limit, offset),
    )
    return [_row_to_food_log(row) for row in cursor.fetchall()]


def list_food_logs_by_user_recent(
    conn: sqlite3.Connection,
    user_id: int,
    *,
    limit: int,
    offset: int = 0,
) -> list[dict[str, object]]:
    return list_food_logs_by_user(
        conn,
        user_id,
        limit=limit,
        offset=offset,
    )


def _serialize_ingredients(value: str | Sequence[dict[str, object]]) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(list(value), ensure_ascii=False)


def _row_to_food_log(row: sqlite3.Row | None) -> dict[str, object] | None:
    if row is None:
        return None
    return dict(row)
