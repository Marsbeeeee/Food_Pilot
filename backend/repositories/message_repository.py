import sqlite3


def create_message(
    conn: sqlite3.Connection,
    session_id: int,
    user_id: int,
    role: str,
    message_type: str,
    *,
    content: str | None = None,
    result_title: str | None = None,
    result_confidence: str | None = None,
    result_description: str | None = None,
    result_items_json: str | None = None,
    result_total: str | None = None,
    created_at: str | None = None,
    auto_commit: bool = True,
) -> dict[str, object]:
    message_columns = _get_table_columns(conn, "messages")
    insert_columns = [
        "session_id",
        "user_id",
        "role",
        "message_type",
        "content",
        "result_title",
        "result_confidence",
        "result_description",
        "result_items_json",
        "result_total",
    ]
    insert_values: list[object] = [
        session_id,
        user_id,
        role,
        message_type,
        content,
        result_title,
        result_confidence,
        result_description,
        result_items_json,
        result_total,
    ]

    if "time" in message_columns:
        insert_columns.append("time")
        insert_values.append(created_at)

    insert_columns.append("created_at")
    insert_values.append(created_at)

    placeholders = [
        "COALESCE(?, CURRENT_TIMESTAMP)" if column in {"time", "created_at"} else "?"
        for column in insert_columns
    ]

    cursor = conn.cursor()
    cursor.execute(
        f"""
        INSERT INTO messages (
            {", ".join(insert_columns)}
        ) VALUES ({", ".join(placeholders)})
        """,
        tuple(insert_values),
    )
    if auto_commit:
        conn.commit()
    message = get_message_by_id(conn, cursor.lastrowid, user_id)
    if message is None:
        raise LookupError("message not found after insert")
    return message


def list_messages_by_session(
    conn: sqlite3.Connection,
    session_id: int,
    user_id: int,
) -> list[dict[str, object]]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            m.id,
            m.session_id,
            m.user_id,
            m.role,
            m.message_type,
            m.content,
            m.result_title,
            m.result_confidence,
            m.result_description,
            m.result_items_json,
            m.result_total,
            m.created_at
        FROM messages AS m
        INNER JOIN chat_sessions AS s
            ON s.id = m.session_id
        WHERE m.session_id = ? AND s.user_id = ?
        ORDER BY m.id ASC
        """,
        (session_id, user_id),
    )
    return [dict(row) for row in cursor.fetchall()]


def delete_messages_by_session(
    conn: sqlite3.Connection,
    session_id: int,
    user_id: int,
) -> int:
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM messages
        WHERE session_id = ?
        AND session_id IN (
            SELECT id
            FROM chat_sessions
            WHERE id = ? AND user_id = ?
        )
        """,
        (session_id, session_id, user_id),
    )
    conn.commit()
    return cursor.rowcount


def get_message_by_id(
    conn: sqlite3.Connection,
    message_id: int,
    user_id: int,
) -> dict[str, object] | None:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            m.id,
            m.session_id,
            m.user_id,
            m.role,
            m.message_type,
            m.content,
            m.result_title,
            m.result_confidence,
            m.result_description,
            m.result_items_json,
            m.result_total,
            m.created_at
        FROM messages AS m
        INNER JOIN chat_sessions AS s
            ON s.id = m.session_id
        WHERE m.id = ? AND s.user_id = ?
        """,
        (message_id, user_id),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return dict(row)

def _get_table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {str(row[1]) for row in cursor.fetchall()}
