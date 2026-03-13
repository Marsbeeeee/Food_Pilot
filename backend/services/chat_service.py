from backend.database.connection import get_db_connection
from backend.repositories.chat_session_repository import (
    create_session as create_session_record,
    delete_session as delete_session_record,
    get_session_by_id as get_session_by_id_record,
    list_sessions_by_user as list_sessions_by_user_record,
    update_session_title as update_session_title_record,
)
from backend.repositories.message_repository import (
    create_message as create_message_record,
    list_messages_by_session as list_messages_by_session_record,
)


DEFAULT_SESSION_TITLE = "New chat"
MAX_SESSION_TITLE_LENGTH = 120


def create_empty_session(user_id: int) -> dict[str, object]:
    conn = get_db_connection()
    try:
        return create_session_record(conn, user_id, DEFAULT_SESSION_TITLE)
    finally:
        conn.close()


def create_session_with_first_user_message(
    user_id: int,
    content: str,
    *,
    created_at: str | None = None,
) -> dict[str, object]:
    conn = get_db_connection()
    try:
        session = create_session_record(conn, user_id, DEFAULT_SESSION_TITLE)
        _append_user_message_with_conn(
            conn,
            user_id,
            int(session["id"]),
            content,
            created_at=created_at,
        )
        return _get_session_detail_with_conn(conn, int(session["id"]), user_id)
    finally:
        conn.close()


def append_user_message(
    user_id: int,
    session_id: int,
    content: str,
    *,
    created_at: str | None = None,
) -> dict[str, object] | None:
    conn = get_db_connection()
    try:
        return _append_user_message_with_conn(
            conn,
            user_id,
            session_id,
            content,
            created_at=created_at,
        )
    finally:
        conn.close()


def append_assistant_message(
    user_id: int,
    session_id: int,
    *,
    message_type: str = "text",
    content: str | None = None,
    result_title: str | None = None,
    result_confidence: str | None = None,
    result_description: str | None = None,
    result_items_json: str | None = None,
    result_total: str | None = None,
    created_at: str | None = None,
) -> dict[str, object] | None:
    conn = get_db_connection()
    try:
        session = get_session_by_id_record(conn, session_id, user_id)
        if session is None:
            return None

        return create_message_record(
            conn,
            session_id,
            user_id,
            "assistant",
            message_type,
            content=content,
            result_title=result_title,
            result_confidence=result_confidence,
            result_description=result_description,
            result_items_json=result_items_json,
            result_total=result_total,
            created_at=created_at,
        )
    finally:
        conn.close()


def rename_session(
    user_id: int,
    session_id: int,
    title: str,
) -> dict[str, object] | None:
    conn = get_db_connection()
    try:
        return update_session_title_record(conn, session_id, user_id, _normalize_title(title))
    finally:
        conn.close()


def delete_session(user_id: int, session_id: int) -> bool:
    conn = get_db_connection()
    try:
        return delete_session_record(conn, session_id, user_id)
    finally:
        conn.close()


def get_session_detail(
    user_id: int,
    session_id: int,
) -> dict[str, object] | None:
    conn = get_db_connection()
    try:
        return _get_session_detail_with_conn(conn, session_id, user_id)
    finally:
        conn.close()


def list_user_sessions(user_id: int) -> list[dict[str, object]]:
    conn = get_db_connection()
    try:
        return list_sessions_by_user_record(conn, user_id)
    finally:
        conn.close()


def _append_user_message_with_conn(
    conn,
    user_id: int,
    session_id: int,
    content: str,
    *,
    created_at: str | None = None,
) -> dict[str, object] | None:
    session = get_session_by_id_record(conn, session_id, user_id)
    if session is None:
        return None

    existing_messages = list_messages_by_session_record(conn, session_id, user_id)
    message = create_message_record(
        conn,
        session_id,
        user_id,
        "user",
        "text",
        content=content,
        created_at=created_at,
    )

    if not existing_messages:
        update_session_title_record(
            conn,
            session_id,
            user_id,
            _build_title_from_first_message(content),
        )

    return message


def _get_session_detail_with_conn(
    conn,
    session_id: int,
    user_id: int,
) -> dict[str, object] | None:
    session = get_session_by_id_record(conn, session_id, user_id)
    if session is None:
        return None

    session_detail = dict(session)
    session_detail["messages"] = list_messages_by_session_record(conn, session_id, user_id)
    return session_detail


def _build_title_from_first_message(content: str) -> str:
    normalized = _normalize_title(content)
    if len(normalized) <= MAX_SESSION_TITLE_LENGTH:
        return normalized
    return f"{normalized[: MAX_SESSION_TITLE_LENGTH - 3]}..."


def _normalize_title(value: str) -> str:
    return " ".join(value.strip().split())
