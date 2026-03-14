import json

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
DEFAULT_ASSISTANT_ERROR_MESSAGE = "Unable to process this meal description right now. Please try again."


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


def create_session_and_reply(
    user_id: int,
    content: str,
    *,
    profile_id: int | None = None,
) -> dict[str, object]:
    conn = get_db_connection()
    try:
        session_detail = create_session_with_first_user_message(
            user_id,
            content,
        )
        session_id = int(session_detail["id"])
        user_message = session_detail["messages"][0]
        assistant_message = _generate_assistant_reply_with_conn(
            conn,
            user_id,
            session_id,
            content,
            profile_id,
        )
        session = _get_session_detail_with_conn(conn, session_id, user_id)
        return {
            "session": session,
            "user_message": user_message,
            "assistant_message": assistant_message,
        }
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


def send_message_in_session(
    user_id: int,
    session_id: int,
    content: str,
    *,
    profile_id: int | None = None,
) -> dict[str, object] | None:
    conn = get_db_connection()
    try:
        user_message = _append_user_message_with_conn(
            conn,
            user_id,
            session_id,
            content,
        )
        if user_message is None:
            return None

        assistant_message = _generate_assistant_reply_with_conn(
            conn,
            user_id,
            session_id,
            content,
            profile_id,
        )
        session = _get_session_detail_with_conn(conn, session_id, user_id)
        return {
            "session": session,
            "user_message": user_message,
            "assistant_message": assistant_message,
        }
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

        message = create_message_record(
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
            auto_commit=message_type != "estimate_result",
        )
        if message_type == "estimate_result":
            conn.commit()
        return message
    except Exception:
        conn.rollback()
        raise
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


def _generate_assistant_reply_with_conn(
    conn,
    user_id: int,
    session_id: int,
    content: str,
    profile_id: int | None,
) -> dict[str, object]:
    try:
        estimate = estimate_meal(content, profile_id, user_id)
        assistant_message = _create_estimate_result_message_with_conn(
            conn,
            user_id,
            session_id,
            estimate=estimate,
        )
    except Exception as exc:
        conn.rollback()
        assistant_message = create_message_record(
            conn,
            session_id,
            user_id,
            "assistant",
            "text",
            content=_build_fallback_message(exc),
        )
    return assistant_message


def _create_estimate_result_message_with_conn(
    conn,
    user_id: int,
    session_id: int,
    *,
    estimate,
) -> dict[str, object]:
    # Chat analysis results stay in the conversation only. Food Log is an explicit
    # save action and must not be created automatically from successful analysis.
    assistant_message = create_message_record(
        conn,
        session_id,
        user_id,
        "assistant",
        "estimate_result",
        content=estimate.suggestion,
        result_title=estimate.title,
        result_confidence=estimate.confidence,
        result_description=estimate.description,
        result_items_json=json.dumps(
            [item.model_dump() for item in estimate.items],
            ensure_ascii=False,
        ),
        result_total=estimate.total_calories,
        auto_commit=False,
    )
    conn.commit()
    return assistant_message


def _build_fallback_message(error: Exception) -> str:
    user_message = getattr(error, "user_message", None)
    if isinstance(user_message, str) and user_message.strip():
        return user_message
    return DEFAULT_ASSISTANT_ERROR_MESSAGE


def _build_title_from_first_message(content: str) -> str:
    normalized = _normalize_title(content)
    if len(normalized) <= MAX_SESSION_TITLE_LENGTH:
        return normalized
    return f"{normalized[: MAX_SESSION_TITLE_LENGTH - 3]}..."


def _normalize_title(value: str) -> str:
    return " ".join(value.strip().split())


def estimate_meal(query: str, profile_id: int | None, user_id: int):
    from backend.services.estimate import estimate_meal as estimate_meal_impl

    return estimate_meal_impl(query, profile_id, user_id)
