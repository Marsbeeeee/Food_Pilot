import sqlite3


def create_session(
    conn: sqlite3.Connection,
    user_id: int,
    title: str,
) -> dict[str, object]:
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO chat_sessions (
            user_id,
            title
        ) VALUES (?, ?)
        """,
        (user_id, title),
    )
    conn.commit()
    return get_session_by_id(conn, cursor.lastrowid, user_id)


def list_sessions_by_user(
    conn: sqlite3.Connection,
    user_id: int,
) -> list[dict[str, object]]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id,
            user_id,
            title,
            created_at,
            updated_at,
            last_message_at,
            deleted_at
        FROM chat_sessions
        WHERE user_id = ?
        ORDER BY last_message_at DESC, id DESC
        """,
        (user_id,),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_session_by_id(
    conn: sqlite3.Connection,
    session_id: int,
    user_id: int,
) -> dict[str, object] | None:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id,
            user_id,
            title,
            created_at,
            updated_at,
            last_message_at,
            deleted_at
        FROM chat_sessions
        WHERE id = ? AND user_id = ?
        """,
        (session_id, user_id),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return dict(row)


def update_session_title(
    conn: sqlite3.Connection,
    session_id: int,
    user_id: int,
    title: str,
) -> dict[str, object] | None:
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE chat_sessions
        SET title = ?
        WHERE id = ? AND user_id = ?
        """,
        (title, session_id, user_id),
    )
    conn.commit()
    if cursor.rowcount == 0:
        return None
    return get_session_by_id(conn, session_id, user_id)


def delete_session(
    conn: sqlite3.Connection,
    session_id: int,
    user_id: int,
) -> bool:
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM chat_sessions
        WHERE id = ? AND user_id = ?
        """,
        (session_id, user_id),
    )
    conn.commit()
    return cursor.rowcount > 0


def touch_session_activity(
    conn: sqlite3.Connection,
    session_id: int,
    last_message_at: str,
) -> bool:
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE chat_sessions
        SET last_message_at = ?
        WHERE id = ?
        """,
        (last_message_at, session_id),
    )
    conn.commit()
    return cursor.rowcount > 0
