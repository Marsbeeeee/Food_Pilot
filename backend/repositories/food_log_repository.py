import json
import sqlite3
from collections.abc import Sequence
from datetime import UTC, date, datetime, timedelta

from backend.text import normalize_food_log_query


ACTIVE_FOOD_LOG_STATUS = "active"
DELETED_FOOD_LOG_STATUS = "deleted"

FOOD_LOG_SELECT_COLUMNS = """
    id,
    user_id,
    session_id,
    source_message_id,
    meal_description,
    normalized_query,
    meal_occurred_at,
    logged_at,
    status,
    result_title,
    result_confidence,
    result_description,
    total_calories,
    ingredients_json,
    source_type,
    is_manual,
    idempotency_key,
    assistant_suggestion,
    created_at,
    updated_at,
    deleted_at
"""

FOOD_LOG_ACTIVE_FILTER = (
    f"status = '{ACTIVE_FOOD_LOG_STATUS}' AND deleted_at IS NULL"
)
FOOD_LOG_DEFAULT_ORDER_BY = "updated_at DESC, created_at DESC, id DESC"


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
    meal_occurred_at: str | None = None,
    logged_at: str | None = None,
    created_at: str | None = None,
    status: str = ACTIVE_FOOD_LOG_STATUS,
    idempotency_key: str | None = None,
    is_manual: bool | None = None,
    auto_commit: bool = True,
) -> dict[str, object]:
    normalized_query = normalize_food_log_query(meal_description)
    resolved_status = _normalize_status(status)
    resolved_logged_at = logged_at or created_at
    resolved_meal_occurred_at = meal_occurred_at or logged_at or created_at
    resolved_is_manual = _resolve_is_manual(source_type, is_manual)
    resolved_idempotency_key = _resolve_idempotency_key(
        source_type,
        source_message_id,
        idempotency_key,
    )
    existing = _get_food_log_by_idempotency_key(
        conn,
        user_id,
        resolved_idempotency_key,
        include_deleted=True,
    )
    if existing is not None:
        if _is_deleted_food_log(existing):
            raise ValueError("idempotency_key already belongs to a deleted food log")
        return existing

    resolved_deleted_at = _resolve_deleted_at(
        resolved_status,
        deleted_at=None,
        fallback=resolved_logged_at or created_at,
    )
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO food_logs (
            user_id,
            session_id,
            source_message_id,
            meal_description,
            normalized_query,
            meal_occurred_at,
            logged_at,
            status,
            result_title,
            result_confidence,
            result_description,
            total_calories,
            ingredients_json,
            source_type,
            is_manual,
            idempotency_key,
            assistant_suggestion,
            created_at,
            updated_at,
            deleted_at
        ) VALUES (
            ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), COALESCE(?, CURRENT_TIMESTAMP), ?,
            ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), COALESCE(?, CURRENT_TIMESTAMP), ?
        )
        """,
        (
            user_id,
            session_id,
            source_message_id,
            meal_description,
            normalized_query,
            resolved_meal_occurred_at,
            resolved_logged_at,
            resolved_status,
            result_title,
            result_confidence,
            result_description,
            total_calories,
            _serialize_ingredients(ingredients),
            source_type,
            int(resolved_is_manual),
            resolved_idempotency_key,
            assistant_suggestion,
            created_at,
            created_at,
            resolved_deleted_at,
        ),
    )
    if auto_commit:
        conn.commit()
    food_log = get_food_log_by_id(
        conn,
        cursor.lastrowid,
        user_id,
        include_deleted=resolved_status == DELETED_FOOD_LOG_STATUS,
    )
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
    food_log_id: int | None = None,
    session_id: int | None = None,
    source_message_id: int | None = None,
    result_confidence: str | None = None,
    assistant_suggestion: str | None = None,
    meal_occurred_at: str | None = None,
    logged_at: str | None = None,
    created_at: str | None = None,
    status: str = ACTIVE_FOOD_LOG_STATUS,
    idempotency_key: str | None = None,
    is_manual: bool | None = None,
    auto_commit: bool = True,
) -> dict[str, object]:
    if food_log_id is not None:
        return update_food_log(
            conn,
            food_log_id,
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
            meal_occurred_at=meal_occurred_at,
            logged_at=logged_at,
            status=status,
            idempotency_key=idempotency_key,
            is_manual=is_manual,
            auto_commit=auto_commit,
        )

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
        meal_occurred_at=meal_occurred_at,
        logged_at=logged_at,
        created_at=created_at,
        status=status,
        idempotency_key=idempotency_key,
        is_manual=is_manual,
        auto_commit=auto_commit,
    )


def update_food_log(
    conn: sqlite3.Connection,
    food_log_id: int,
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
    meal_occurred_at: str | None = None,
    logged_at: str | None = None,
    status: str = ACTIVE_FOOD_LOG_STATUS,
    idempotency_key: str | None = None,
    is_manual: bool | None = None,
    auto_commit: bool = True,
) -> dict[str, object]:
    existing = get_food_log_by_id(conn, food_log_id, user_id, include_deleted=True)
    if existing is None:
        raise LookupError("food log not found")
    if _is_deleted_food_log(existing):
        raise LookupError("food log entry has been deleted")

    resolved_session_id = (
        existing["session_id"]
        if session_id is None
        else session_id
    )
    resolved_source_message_id = (
        existing["source_message_id"]
        if source_message_id is None
        else source_message_id
    )
    resolved_result_confidence = (
        existing["result_confidence"]
        if result_confidence is None
        else result_confidence
    )
    resolved_assistant_suggestion = (
        existing["assistant_suggestion"]
        if assistant_suggestion is None
        else assistant_suggestion
    )
    resolved_logged_at = (
        existing["logged_at"]
        if logged_at is None
        else logged_at
    )
    resolved_meal_occurred_at = (
        existing["meal_occurred_at"]
        if meal_occurred_at is None
        else meal_occurred_at
    )
    resolved_status = _normalize_status(status or str(existing["status"]))
    resolved_is_manual = _resolve_is_manual(
        source_type,
        bool(existing["is_manual"]) if is_manual is None else is_manual,
    )
    resolved_idempotency_key = _resolve_idempotency_key(
        source_type,
        resolved_source_message_id,
        idempotency_key if idempotency_key is not None else existing["idempotency_key"],
    )
    duplicate = _get_food_log_by_idempotency_key(
        conn,
        user_id,
        resolved_idempotency_key,
        include_deleted=True,
    )
    if duplicate is not None and int(duplicate["id"]) != food_log_id:
        if _is_deleted_food_log(duplicate):
            raise ValueError("idempotency_key already belongs to a deleted food log")
        raise ValueError("idempotency_key already belongs to another food log")

    resolved_deleted_at = _resolve_deleted_at(
        resolved_status,
        deleted_at=existing["deleted_at"],
        fallback=resolved_logged_at or str(existing["created_at"]),
    )
    normalized_query = normalize_food_log_query(meal_description)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE food_logs
        SET
            session_id = ?,
            source_message_id = ?,
            meal_description = ?,
            normalized_query = ?,
            meal_occurred_at = ?,
            logged_at = ?,
            status = ?,
            result_title = ?,
            result_confidence = ?,
            result_description = ?,
            total_calories = ?,
            ingredients_json = ?,
            source_type = ?,
            is_manual = ?,
            idempotency_key = ?,
            assistant_suggestion = ?,
            deleted_at = ?
        WHERE id = ? AND user_id = ?
        """,
        (
            resolved_session_id,
            resolved_source_message_id,
            meal_description,
            normalized_query,
            resolved_meal_occurred_at,
            resolved_logged_at,
            resolved_status,
            result_title,
            resolved_result_confidence,
            result_description,
            total_calories,
            _serialize_ingredients(ingredients),
            source_type,
            int(resolved_is_manual),
            resolved_idempotency_key,
            resolved_assistant_suggestion,
            resolved_deleted_at,
            food_log_id,
            user_id,
        ),
    )
    if cursor.rowcount == 0:
        raise LookupError("food log not found")
    if auto_commit:
        conn.commit()
    food_log = get_food_log_by_id(
        conn,
        food_log_id,
        user_id,
        include_deleted=resolved_status == DELETED_FOOD_LOG_STATUS,
    )
    if food_log is None:
        raise LookupError("food log not found after save")
    return food_log


def get_food_log_by_id(
    conn: sqlite3.Connection,
    food_log_id: int,
    user_id: int,
    *,
    include_deleted: bool = False,
) -> dict[str, object] | None:
    cursor = conn.cursor()
    query = f"""
        SELECT
            {FOOD_LOG_SELECT_COLUMNS}
        FROM food_logs
        WHERE id = ? AND user_id = ?
    """
    parameters: list[object] = [food_log_id, user_id]
    if not include_deleted:
        query += f" AND {FOOD_LOG_ACTIVE_FILTER}"
    cursor.execute(query, tuple(parameters))
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
        WHERE user_id = ? AND {FOOD_LOG_ACTIVE_FILTER}
    """
    parameters: list[object] = [user_id]

    if session_id is not None:
        query += " AND session_id = ?"
        parameters.append(session_id)

    if date_from is not None:
        query += " AND meal_occurred_at >= ?"
        parameters.append(f"{date_from.isoformat()} 00:00:00")

    if date_to is not None:
        query += " AND meal_occurred_at < ?"
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

    cursor.execute(query, tuple(parameters))
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
        WHERE user_id = ? AND session_id = ? AND {FOOD_LOG_ACTIVE_FILTER}
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


def delete_food_log(
    conn: sqlite3.Connection,
    food_log_id: int,
    user_id: int,
    *,
    auto_commit: bool = True,
) -> bool:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        UPDATE food_logs
        SET
            status = '{DELETED_FOOD_LOG_STATUS}',
            deleted_at = CURRENT_TIMESTAMP
        WHERE id = ? AND user_id = ? AND {FOOD_LOG_ACTIVE_FILTER}
        """,
        (food_log_id, user_id),
    )
    if auto_commit:
        conn.commit()
    return cursor.rowcount > 0


def restore_food_log(
    conn: sqlite3.Connection,
    food_log_id: int,
    user_id: int,
    *,
    auto_commit: bool = True,
) -> dict[str, object]:
    existing = get_food_log_by_id(conn, food_log_id, user_id, include_deleted=True)
    if existing is None:
        raise LookupError("food log not found")
    if not _is_deleted_food_log(existing):
        return existing

    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE food_logs
        SET
            status = ?,
            deleted_at = NULL
        WHERE id = ? AND user_id = ?
        """,
        (ACTIVE_FOOD_LOG_STATUS, food_log_id, user_id),
    )
    if cursor.rowcount == 0:
        raise LookupError("food log not found")
    if auto_commit:
        conn.commit()

    restored = get_food_log_by_id(conn, food_log_id, user_id, include_deleted=False)
    if restored is None:
        raise LookupError("food log not found after restore")
    return restored


def _serialize_ingredients(value: str | Sequence[dict[str, object]]) -> str:
    if isinstance(value, str):
        return value
    return json.dumps(list(value), ensure_ascii=False)


def _row_to_food_log(row: sqlite3.Row | None) -> dict[str, object] | None:
    if row is None:
        return None
    food_log = dict(row)
    if "is_manual" in food_log:
        food_log["is_manual"] = bool(food_log["is_manual"])
    return food_log


def _escape_like_value(value: str) -> str:
    return (
        value.replace("\\", "\\\\")
        .replace("%", "\\%")
        .replace("_", "\\_")
    )


def _get_food_log_by_idempotency_key(
    conn: sqlite3.Connection,
    user_id: int,
    idempotency_key: str | None,
    *,
    include_deleted: bool,
) -> dict[str, object] | None:
    normalized_key = _normalize_idempotency_key(idempotency_key)
    if normalized_key is None:
        return None

    cursor = conn.cursor()
    query = f"""
        SELECT
            {FOOD_LOG_SELECT_COLUMNS}
        FROM food_logs
        WHERE user_id = ? AND idempotency_key = ?
    """
    parameters: list[object] = [user_id, normalized_key]
    if not include_deleted:
        query += f" AND {FOOD_LOG_ACTIVE_FILTER}"
    query += " ORDER BY id DESC LIMIT 1"
    cursor.execute(query, tuple(parameters))
    return _row_to_food_log(cursor.fetchone())


def _resolve_idempotency_key(
    source_type: str,
    source_message_id: int | None,
    idempotency_key: str | None,
) -> str | None:
    normalized_key = _normalize_idempotency_key(idempotency_key)
    if normalized_key is not None:
        return normalized_key
    if source_type == "chat_message" and source_message_id is not None:
        return f"chat_message:{int(source_message_id)}"
    return None


def _normalize_idempotency_key(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _normalize_status(value: str | None) -> str:
    normalized = (value or ACTIVE_FOOD_LOG_STATUS).strip().lower()
    if normalized not in {ACTIVE_FOOD_LOG_STATUS, DELETED_FOOD_LOG_STATUS}:
        raise ValueError("status must be active or deleted")
    return normalized


def _resolve_is_manual(source_type: str, is_manual: bool | None) -> bool:
    if is_manual is not None:
        return bool(is_manual)
    return source_type == "manual"


def _resolve_deleted_at(
    status: str,
    *,
    deleted_at: object,
    fallback: str | None,
) -> str | None:
    if status != DELETED_FOOD_LOG_STATUS:
        return None
    if isinstance(deleted_at, str) and deleted_at.strip():
        return deleted_at
    if fallback:
        return fallback
    return _current_timestamp()


def _is_deleted_food_log(entry: dict[str, object]) -> bool:
    if entry.get("status") == DELETED_FOOD_LOG_STATUS:
        return True
    deleted_at = entry.get("deleted_at")
    return isinstance(deleted_at, str) and bool(deleted_at.strip())


def _current_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
