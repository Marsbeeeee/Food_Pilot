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
    title: str,
    description: str,
    items_json: str,
    total: str,
    confidence: str | None = None,
    suggestion: str | None = None,
    session_id: int | None = None,
    message_id: int | None = None,
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
            title=title,
            description=description,
            items_json=items_json,
            total=total,
            confidence=confidence,
            suggestion=suggestion,
            session_id=session_id,
            message_id=message_id,
            created_at=created_at,
        )
    finally:
        if owns_connection:
            active_conn.close()


def record_food_log_entry_from_estimate(
    user_id: int,
    estimate,
    *,
    source_type: str,
    session_id: int | None = None,
    message_id: int | None = None,
    created_at: str | None = None,
    conn: sqlite3.Connection | None = None,
) -> dict[str, object]:
    return record_food_log_entry(
        user_id,
        source_type,
        title=estimate.title,
        description=estimate.description,
        items_json=json.dumps(
            [item.model_dump() for item in estimate.items],
            ensure_ascii=False,
        ),
        total=estimate.total_calories,
        confidence=getattr(estimate, "confidence", None),
        suggestion=getattr(estimate, "suggestion", None),
        session_id=session_id,
        message_id=message_id,
        created_at=created_at,
        conn=conn,
    )


def list_food_log_entries(user_id: int) -> list[dict[str, object]]:
    conn = get_db_connection()
    try:
        return list_food_log_entries_by_user_record(conn, user_id)
    finally:
        conn.close()
