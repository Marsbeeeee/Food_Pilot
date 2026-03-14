import json
import sqlite3
from collections.abc import Sequence
from datetime import date, timedelta


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

FOOD_LOG_DEFAULT_ORDER_BY = "updated_at DESC, id DESC"


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


def save_food_log(
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
    existing_id = _get_food_log_id_by_source_message_id(conn, user_id, source_message_id)
    if existing_id is None:
        return create_food_log(
            conn,
            user_id,
            source_type=source_type,
            meal_description=meal_description,
            result_title=result_title,
            result_description=result_description,
            total_calories=total_calories,
            ingredients=ingredients,
            session_id=session_id,
            source_message_id=source_message_id,
            result_confidence=result_confidence,
            assistant_suggestion=assistant_suggestion,
            logged_at=logged_at,
            created_at=created_at,
            auto_commit=auto_commit,
        )

    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE food_logs
        SET
            session_id = ?,
            meal_description = ?,
            logged_at = COALESCE(?, CURRENT_TIMESTAMP),
            result_title = ?,
            result_confidence = ?,
            result_description = ?,
            total_calories = ?,
            ingredients_json = ?,
            source_type = ?,
            assistant_suggestion = ?
        WHERE id = ? AND user_id = ?
        """,
        (
            session_id,
            meal_description,
            logged_at,
            result_title,
            result_confidence,
            result_description,
            total_calories,
            _serialize_ingredients(ingredients),
            source_type,
            assistant_suggestion,
            existing_id,
            user_id,
        ),
    )
    if auto_commit:
        conn.commit()
    food_log = get_food_log_by_id(conn, existing_id, user_id)
    if food_log is None:
        raise LookupError("food log not found after save")
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
    session_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    meal: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict[str, object]]:
    cursor = conn.cursor()
    query = f"""
        SELECT
            {FOOD_LOG_SELECT_COLUMNS}
        FROM food_logs
        WHERE user_id = ?
    """
    parameters: list[object] = [user_id]

    if session_id is not None:
        query += " AND session_id = ?"
        parameters.append(session_id)

    if date_from is not None:
        query += " AND logged_at >= ?"
        parameters.append(f"{date_from.isoformat()} 00:00:00")

    if date_to is not None:
        query += " AND logged_at < ?"
        parameters.append(f"{(date_to + timedelta(days=1)).isoformat()} 00:00:00")

    if meal:
        query += (
            " AND (meal_description LIKE ? ESCAPE '\\' "
            "OR result_title LIKE ? ESCAPE '\\')"
        )
        keyword = f"%{_escape_like_value(meal)}%"
        parameters.extend([keyword, keyword])

    query += f"""
        ORDER BY {FOOD_LOG_DEFAULT_ORDER_BY}
        LIMIT COALESCE(?, -1) OFFSET ?
    """
    parameters.extend([limit, offset])

    cursor.execute(
        query,
        tuple(parameters),
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
        ORDER BY {FOOD_LOG_DEFAULT_ORDER_BY}
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


def _escape_like_value(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def _get_food_log_id_by_source_message_id(
    conn: sqlite3.Connection,
    user_id: int,
    source_message_id: int | None,
) -> int | None:
    if source_message_id is None:
        return None

    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT id
        FROM food_logs
        WHERE user_id = ? AND source_message_id = ?
        """,
        (user_id, source_message_id),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return int(row["id"])
