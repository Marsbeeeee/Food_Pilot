import json
import sqlite3

from backend.database.connection import get_db_connection
from backend.repositories.food_log_repository import (
    create_food_log_entry as create_food_log_entry_record,
    list_food_log_entries_by_user as list_food_log_entries_by_user_record,
)


def record_food_log_entry(
    user_id: int,
    source_type: str,
    *,
    meal_description: str,
    result_title: str,
    result_description: str,
    total_calories: str,
    ingredients_json: str,
    session_id: int | None = None,
    source_message_id: int | None = None,
    result_confidence: str | None = None,
    assistant_suggestion: str | None = None,
    logged_at: str | None = None,
    created_at: str | None = None,
    conn: sqlite3.Connection | None = None,
) -> dict[str, object]:
    owns_connection = conn is None
    active_conn = conn or get_db_connection()

    try:
        return create_food_log_entry_record(
            active_conn,
            user_id,
            source_type,
            meal_description=meal_description,
            result_title=result_title,
            result_description=result_description,
            total_calories=total_calories,
            ingredients_json=ingredients_json,
            session_id=session_id,
            source_message_id=source_message_id,
            result_confidence=result_confidence,
            assistant_suggestion=assistant_suggestion,
            logged_at=logged_at,
            created_at=created_at,
        )
    finally:
        if owns_connection:
            active_conn.close()


def record_food_log_entry_from_estimate(
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
    return record_food_log_entry(
        user_id,
        source_type,
        meal_description=meal_description,
        result_title=estimate.title,
        result_description=estimate.description,
        total_calories=estimate.total_calories,
        ingredients_json=json.dumps(
            [item.model_dump() for item in estimate.items],
            ensure_ascii=False,
        ),
        session_id=session_id,
        source_message_id=source_message_id,
        result_confidence=getattr(estimate, "confidence", None),
        assistant_suggestion=getattr(estimate, "suggestion", None),
        logged_at=logged_at,
        created_at=created_at,
        conn=conn,
    )


def list_food_log_entries(user_id: int) -> list[dict[str, object]]:
    conn = get_db_connection()
    try:
        return list_food_log_entries_by_user_record(conn, user_id)
    finally:
        conn.close()
