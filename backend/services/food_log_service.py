import sqlite3
from datetime import date

from backend.database.connection import get_db_connection
from backend.repositories.message_repository import get_message_by_id as get_message_by_id_record
from backend.repositories.food_log_repository import (
    create_food_log as create_food_log_record,
    delete_food_log as delete_food_log_record,
    get_food_log_by_id as get_food_log_by_id_record,
    list_food_logs_by_session as list_food_logs_by_session_record,
    list_food_logs_by_user as list_food_logs_by_user_record,
    list_food_logs_by_user_recent as list_food_logs_by_user_recent_record,
    restore_food_log as restore_food_log_record,
    save_food_log as save_food_log_record,
)


def create_food_log(
    user_id: int,
    source_type: str,
    *,
    meal_description: str,
    result_title: str,
    result_description: str,
    total_calories: str,
    ingredients: str | list[dict[str, object]],
    session_id: int | None = None,
    source_message_id: int | None = None,
    result_confidence: str | None = None,
    assistant_suggestion: str | None = None,
    meal_occurred_at: str | None = None,
    logged_at: str | None = None,
    created_at: str | None = None,
    status: str = "active",
    idempotency_key: str | None = None,
    is_manual: bool | None = None,
    image: str | None = None,
    image_source: str | None = None,
    image_license: str | None = None,
    conn: sqlite3.Connection | None = None,
    auto_commit: bool = True,
) -> dict[str, object]:
    owns_connection = conn is None
    active_conn = conn or get_db_connection()

    try:
        _validate_food_log_source(
            active_conn,
            user_id,
            source_type=source_type,
            session_id=session_id,
            source_message_id=source_message_id,
            is_manual=is_manual,
        )
        return create_food_log_record(
            active_conn,
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
            image=image,
            image_source=image_source,
            image_license=image_license,
            auto_commit=auto_commit,
        )
    except Exception:
        if owns_connection:
            active_conn.rollback()
        raise
    finally:
        if owns_connection:
            active_conn.close()


def save_food_log(
    user_id: int,
    source_type: str,
    *,
    meal_description: str,
    result_title: str,
    result_description: str,
    total_calories: str,
    ingredients: str | list[dict[str, object]],
    food_log_id: int | None = None,
    session_id: int | None = None,
    source_message_id: int | None = None,
    result_confidence: str | None = None,
    assistant_suggestion: str | None = None,
    meal_occurred_at: str | None = None,
    logged_at: str | None = None,
    created_at: str | None = None,
    status: str = "active",
    idempotency_key: str | None = None,
    is_manual: bool | None = None,
    image: str | None = None,
    image_source: str | None = None,
    image_license: str | None = None,
    conn: sqlite3.Connection | None = None,
    auto_commit: bool = True,
) -> dict[str, object]:
    owns_connection = conn is None
    active_conn = conn or get_db_connection()

    try:
        _validate_food_log_source(
            active_conn,
            user_id,
            source_type=source_type,
            session_id=session_id,
            source_message_id=source_message_id,
            is_manual=is_manual,
        )
        # For chat-originated entries, enforce that the source message actually
        # contains a concrete, structured, reusable meal result before allowing
        # it to be saved into the Food Log.
        if source_type == "chat_message" and source_message_id is not None:
            message = get_message_by_id_record(
                active_conn,
                source_message_id,
                user_id,
            )
            if message is None:
                raise LookupError("source message not found")
            if not can_save_message_to_food_log(message):
                raise ValueError("当前这条回复不包含可复用的菜品结果，无法保存到 Food Log。")
        return save_food_log_record(
            active_conn,
            user_id,
            source_type=source_type,
            meal_description=meal_description,
            result_title=result_title,
            result_description=result_description,
            total_calories=total_calories,
            ingredients=ingredients,
            food_log_id=food_log_id,
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
            image=image,
            image_source=image_source,
            image_license=image_license,
            auto_commit=auto_commit,
        )
    except Exception:
        if owns_connection:
            active_conn.rollback()
        raise
    finally:
        if owns_connection:
            active_conn.close()


def create_food_log_from_estimate(
    user_id: int,
    meal_description: str,
    estimate,
    *,
    source_type: str,
    session_id: int | None = None,
    source_message_id: int | None = None,
    meal_occurred_at: str | None = None,
    logged_at: str | None = None,
    created_at: str | None = None,
    idempotency_key: str | None = None,
    is_manual: bool | None = None,
    image: str | None = None,
    image_source: str | None = None,
    image_license: str | None = None,
    conn: sqlite3.Connection | None = None,
) -> dict[str, object]:
    # Successful chat analysis and `/estimate` responses must not create Food Log
    # rows automatically. Persisting still requires an explicit save action.
    owns_connection = conn is None
    active_conn = conn or get_db_connection()
    try:
        food_log = save_food_log(
            user_id,
            source_type,
            meal_description=meal_description,
            result_title=estimate.title,
            result_description=estimate.description,
            total_calories=estimate.total_calories,
            ingredients=[item.model_dump() for item in estimate.items],
            session_id=session_id,
            source_message_id=source_message_id,
            result_confidence=getattr(estimate, "confidence", None),
            assistant_suggestion=getattr(estimate, "suggestion", None),
            meal_occurred_at=meal_occurred_at,
            logged_at=logged_at,
            created_at=created_at,
            idempotency_key=idempotency_key,
            is_manual=is_manual,
            image=image,
            image_source=image_source,
            image_license=image_license,
            conn=active_conn,
            auto_commit=False,
        )
        if owns_connection:
            active_conn.commit()
        return food_log
    except Exception:
        if owns_connection:
            active_conn.rollback()
        raise
    finally:
        if owns_connection:
            active_conn.close()


def build_estimate_api_idempotency_key(client_request_id: str) -> str:
    normalized = client_request_id.strip()
    if not normalized:
        raise ValueError("client_request_id cannot be empty")
    if normalized.startswith("estimate_api:"):
        return normalized
    return f"estimate_api:{normalized}"


def get_food_log_by_id(
    user_id: int,
    food_log_id: int,
    *,
    include_deleted: bool = False,
) -> dict[str, object] | None:
    conn = get_db_connection()
    try:
        return get_food_log_by_id_record(
            conn,
            food_log_id,
            user_id,
            include_deleted=include_deleted,
        )
    finally:
        conn.close()


def can_save_message_to_food_log(message: dict[str, object]) -> bool:
    """
    Pure helper to decide whether a chat message is eligible to be saved
    as a Food Log entry.

    It encodes the same rules as the product spec:
    - Only structured meal estimate results (meal_estimate / estimate_result)
      with a concrete meal object and structured nutrition data can be saved.
    - Recommendation and text messages are not directly savable.
    """
    message_type = str(message.get("message_type") or "").strip()

    # Accept both the legacy internal "estimate_result" and the external
    # "meal_estimate" naming as estimate-like messages.
    if message_type not in {"estimate_result", "meal_estimate"}:
        return False

    result_title = str(message.get("result_title") or "").strip()
    result_description = str(message.get("result_description") or "").strip()
    result_items_json = str(message.get("result_items_json") or "").strip()
    result_total = str(message.get("result_total") or "").strip()

    if not result_title or not result_description:
        return False
    if not result_items_json or not result_total:
        return False

    return True


def update_food_log_entry(
    user_id: int,
    food_log_id: int,
    *,
    meal_description: str | None = None,
    result_title: str | None = None,
    result_confidence: str | None = None,
    result_description: str | None = None,
    total_calories: str | None = None,
    ingredients: str | list[dict[str, object]] | None = None,
    assistant_suggestion: str | None = None,
    meal_occurred_at: str | None = None,
    image: str | None = None,
    image_source: str | None = None,
    image_license: str | None = None,
    conn: sqlite3.Connection | None = None,
    auto_commit: bool = True,
) -> dict[str, object]:
    owns_connection = conn is None
    active_conn = conn or get_db_connection()

    try:
        existing = get_food_log_by_id_record(
            active_conn,
            food_log_id,
            user_id,
            include_deleted=True,
        )
        if existing is None:
            raise LookupError("food log not found")
        if existing.get("status") == "deleted" or existing.get("deleted_at"):
            raise LookupError("food log entry has been deleted")

        return save_food_log_record(
            active_conn,
            user_id,
            source_type=str(existing["source_type"]),
            meal_description=(
                str(existing["meal_description"])
                if meal_description is None
                else meal_description
            ),
            result_title=(
                str(existing["result_title"])
                if result_title is None
                else result_title
            ),
            result_description=(
                str(existing["result_description"])
                if result_description is None
                else result_description
            ),
            total_calories=(
                str(existing["total_calories"])
                if total_calories is None
                else total_calories
            ),
            ingredients=(
                str(existing["ingredients_json"])
                if ingredients is None
                else ingredients
            ),
            food_log_id=food_log_id,
            session_id=existing["session_id"],
            source_message_id=existing["source_message_id"],
            result_confidence=(
                existing["result_confidence"]
                if result_confidence is None
                else result_confidence
            ),
            assistant_suggestion=(
                existing["assistant_suggestion"]
                if assistant_suggestion is None
                else assistant_suggestion
            ),
            meal_occurred_at=(
                str(existing["meal_occurred_at"])
                if meal_occurred_at is None and existing["meal_occurred_at"] is not None
                else meal_occurred_at
            ),
            logged_at=existing["logged_at"],
            status=str(existing["status"]),
            idempotency_key=(
                str(existing["idempotency_key"])
                if existing["idempotency_key"] is not None
                else None
            ),
            is_manual=bool(existing["is_manual"]),
            image=(
                existing.get("image")
                if image is None
                else image
            ),
            image_source=(
                existing.get("image_source")
                if image_source is None
                else image_source
            ),
            image_license=(
                existing.get("image_license")
                if image_license is None
                else image_license
            ),
            auto_commit=auto_commit,
        )
    except Exception:
        if owns_connection:
            active_conn.rollback()
        raise
    finally:
        if owns_connection:
            active_conn.close()


def delete_food_log(
    user_id: int,
    food_log_id: int,
    *,
    conn: sqlite3.Connection | None = None,
    auto_commit: bool = True,
) -> bool:
    owns_connection = conn is None
    active_conn = conn or get_db_connection()

    try:
        # Food Log deletion is soft-delete only so the row still carries
        # lifecycle state for audit and idempotency.
        return delete_food_log_record(
            active_conn,
            food_log_id,
            user_id,
            auto_commit=auto_commit,
        )
    except Exception:
        if owns_connection:
            active_conn.rollback()
        raise
    finally:
        if owns_connection:
            active_conn.close()


def restore_food_log(
    user_id: int,
    food_log_id: int,
    *,
    conn: sqlite3.Connection | None = None,
    auto_commit: bool = True,
) -> dict[str, object]:
    owns_connection = conn is None
    active_conn = conn or get_db_connection()

    try:
        return restore_food_log_record(
            active_conn,
            food_log_id,
            user_id,
            auto_commit=auto_commit,
        )
    except Exception:
        if owns_connection:
            active_conn.rollback()
        raise
    finally:
        if owns_connection:
            active_conn.close()


def list_food_logs_by_user(
    user_id: int,
    *,
    session_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    query: str | None = None,
    meal: str | None = None,
    sort: str = "created_desc",
    limit: int | None = None,
    offset: int = 0,
) -> list[dict[str, object]]:
    conn = get_db_connection()
    try:
        resolved_query = query if query is not None else meal
        return list_food_logs_by_user_record(
            conn,
            user_id,
            session_id=session_id,
            date_from=date_from,
            date_to=date_to,
            query_text=resolved_query,
            sort=sort,
            limit=limit,
            offset=offset,
        )
    finally:
        conn.close()


def list_food_logs_by_session(
    user_id: int,
    session_id: int,
    *,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict[str, object]]:
    conn = get_db_connection()
    try:
        return list_food_logs_by_session_record(
            conn,
            user_id,
            session_id,
            limit=limit,
            offset=offset,
        )
    finally:
        conn.close()


def list_recent_food_logs(
    user_id: int,
    *,
    limit: int,
    offset: int = 0,
) -> list[dict[str, object]]:
    conn = get_db_connection()
    try:
        return list_food_logs_by_user_recent_record(
            conn,
            user_id,
            limit=limit,
            offset=offset,
        )
    finally:
        conn.close()


def _validate_food_log_source(
    conn: sqlite3.Connection,
    user_id: int,
    *,
    source_type: str,
    session_id: int | None,
    source_message_id: int | None,
    is_manual: bool | None,
) -> None:
    if source_type not in {"estimate_api", "chat_message", "manual"}:
        raise ValueError("source_type must be estimate_api, chat_message, or manual")

    if source_type == "chat_message" and session_id is None:
        raise ValueError("session_id is required for chat_message saves")

    if source_type != "chat_message" and source_message_id is not None:
        raise ValueError("source_message_id is only supported for chat_message saves")

    if source_type == "manual" and is_manual is False:
        raise ValueError("manual saves must set is_manual to true when provided")

    if source_type != "manual" and is_manual is True:
        raise ValueError("is_manual can only be true for manual saves")

    if source_message_id is None:
        return

    source_message = get_message_by_id_record(conn, source_message_id, user_id)
    if source_message is None:
        raise LookupError("Chat analysis not found")

    if int(source_message["session_id"]) != session_id:
        raise ValueError("source_message_id does not belong to the provided session_id")

    if source_message["role"] != "assistant" or source_message["message_type"] != "estimate_result":
        raise ValueError("source_message_id must reference an assistant estimate result")
