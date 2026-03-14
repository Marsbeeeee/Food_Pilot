import sqlite3
from datetime import date

from backend.database.connection import get_db_connection
from backend.repositories.food_log_repository import (
    create_food_log as create_food_log_record,
    get_food_log_by_id as get_food_log_by_id_record,
    list_food_logs_by_session as list_food_logs_by_session_record,
    list_food_logs_by_user as list_food_logs_by_user_record,
    list_food_logs_by_user_recent as list_food_logs_by_user_recent_record,
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
    logged_at: str | None = None,
    created_at: str | None = None,
    conn: sqlite3.Connection | None = None,
    auto_commit: bool = True,
) -> dict[str, object]:
    owns_connection = conn is None
    active_conn = conn or get_db_connection()

    try:
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
            logged_at=logged_at,
            created_at=created_at,
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
    logged_at: str | None = None,
    created_at: str | None = None,
    conn: sqlite3.Connection | None = None,
) -> dict[str, object]:
    # Food Log writes are save-only. Successful chat analysis and `/estimate`
    # responses must not call this automatically.
    owns_connection = conn is None
    active_conn = conn or get_db_connection()
    try:
        food_log = create_food_log(
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
            logged_at=logged_at,
            created_at=created_at,
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


def get_food_log_by_id(user_id: int, food_log_id: int) -> dict[str, object] | None:
    conn = get_db_connection()
    try:
        return get_food_log_by_id_record(conn, food_log_id, user_id)
    finally:
        conn.close()


def list_food_logs_by_user(
    user_id: int,
    *,
    session_id: int | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    meal: str | None = None,
    limit: int | None = None,
    offset: int = 0,
) -> list[dict[str, object]]:
    conn = get_db_connection()
    try:
        return list_food_logs_by_user_record(
            conn,
            user_id,
            session_id=session_id,
            date_from=date_from,
            date_to=date_to,
            meal=meal,
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
