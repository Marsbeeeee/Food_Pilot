import json
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
    payload_json: str | None = None,
    created_at: str | None = None,
    auto_commit: bool = True,
) -> dict[str, object]:
    message_columns = _get_table_columns(conn, "messages")
    resolved_payload_json = _build_payload_json(
        message_type,
        content=content,
        payload_json=payload_json,
        result_title=result_title,
        result_confidence=result_confidence,
        result_description=result_description,
        result_items_json=result_items_json,
        result_total=result_total,
    )
    insert_columns = [
        "session_id",
        "user_id",
        "role",
        "message_type",
        "content",
    ]
    insert_values: list[object] = [
        session_id,
        user_id,
        role,
        message_type,
        content,
    ]

    if "payload_json" in message_columns:
        insert_columns.append("payload_json")
        insert_values.append(resolved_payload_json)

    insert_columns.extend(
        [
            "result_title",
            "result_confidence",
            "result_description",
            "result_items_json",
            "result_total",
        ]
    )
    insert_values.extend(
        [
            result_title,
            result_confidence,
            result_description,
            result_items_json,
            result_total,
        ]
    )

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
    payload_json_select = _get_payload_json_select(conn)
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            m.id,
            m.session_id,
            m.user_id,
            m.role,
            m.message_type,
            m.content,
            {payload_json_select},
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
    return [_serialize_message_row(dict(row)) for row in cursor.fetchall()]


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
    payload_json_select = _get_payload_json_select(conn)
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            m.id,
            m.session_id,
            m.user_id,
            m.role,
            m.message_type,
            m.content,
            {payload_json_select},
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
    return _serialize_message_row(dict(row))


def _get_table_columns(conn: sqlite3.Connection, table_name: str) -> set[str]:
    cursor = conn.cursor()
    cursor.execute(f"PRAGMA table_info({table_name})")
    return {str(row[1]) for row in cursor.fetchall()}


def _get_payload_json_select(conn: sqlite3.Connection) -> str:
    if "payload_json" in _get_table_columns(conn, "messages"):
        return "m.payload_json"
    return "NULL AS payload_json"


def _serialize_message_row(message: dict[str, object]) -> dict[str, object]:
    payload_json = message.get("payload_json")
    if not _has_text(payload_json):
        derived_payload_json = _build_payload_json(
            str(message.get("message_type") or ""),
            content=message.get("content"),
            payload_json=None,
            result_title=message.get("result_title"),
            result_confidence=message.get("result_confidence"),
            result_description=message.get("result_description"),
            result_items_json=message.get("result_items_json"),
            result_total=message.get("result_total"),
        )
        if derived_payload_json is not None:
            message["payload_json"] = derived_payload_json
    return message


def _build_payload_json(
    message_type: str,
    *,
    content: object,
    payload_json: str | None,
    result_title: object,
    result_confidence: object,
    result_description: object,
    result_items_json: object,
    result_total: object,
) -> str | None:
    if _has_text(payload_json):
        return str(payload_json).strip()

    if message_type == "text" and _has_text(content):
        return json.dumps({"text": str(content).strip()}, ensure_ascii=False)

    if message_type not in {"estimate_result", "meal_estimate"}:
        return None

    if not all(
        _has_text(value)
        for value in (
            result_title,
            result_confidence,
            result_description,
            result_items_json,
            result_total,
        )
    ):
        return None

    payload: dict[str, object] = {
        "title": str(result_title).strip(),
        "confidence": str(result_confidence).strip(),
        "description": str(result_description).strip(),
        "total": str(result_total).strip(),
    }
    items = _parse_json_list(str(result_items_json).strip())
    if items is not None:
        payload["items"] = items

    return json.dumps(payload, ensure_ascii=False)


def _parse_json_list(value: str) -> list[object] | None:
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, list):
        return None
    return parsed


def _has_text(value: object) -> bool:
    return isinstance(value, str) and bool(value.strip())
