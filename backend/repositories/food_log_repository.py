import sqlite3


def create_food_log_entry(
    conn: sqlite3.Connection,
    user_id: int,
    source_type: str,
    *,
    title: str,
    description: str,
    items_json: str,
    total: str,
    confidence: str | None = None,
    suggestion: str | None = None,
    session_id: int | None = None,
    message_id: int | None = None,
    created_at: str | None = None,
) -> dict[str, object]:
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO food_log_entries (
            user_id,
            source_type,
            session_id,
            message_id,
            title,
            confidence,
            description,
            items_json,
            total,
            suggestion,
            created_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP))
        """,
        (
            user_id,
            source_type,
            session_id,
            message_id,
            title,
            confidence,
            description,
            items_json,
            total,
            suggestion,
            created_at,
        ),
    )
    conn.commit()
    return get_food_log_entry_by_id(conn, cursor.lastrowid, user_id)


def list_food_log_entries_by_user(
    conn: sqlite3.Connection,
    user_id: int,
) -> list[dict[str, object]]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id,
            user_id,
            source_type,
            session_id,
            message_id,
            title,
            confidence,
            description,
            items_json,
            total,
            suggestion,
            created_at
        FROM food_log_entries
        WHERE user_id = ?
        ORDER BY created_at DESC, id DESC
        """,
        (user_id,),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_food_log_entry_by_id(
    conn: sqlite3.Connection,
    entry_id: int,
    user_id: int,
) -> dict[str, object]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id,
            user_id,
            source_type,
            session_id,
            message_id,
            title,
            confidence,
            description,
            items_json,
            total,
            suggestion,
            created_at
        FROM food_log_entries
        WHERE id = ? AND user_id = ?
        """,
        (entry_id, user_id),
    )
    row = cursor.fetchone()
    if row is None:
        raise LookupError("food log entry not found after insert")
    return dict(row)
