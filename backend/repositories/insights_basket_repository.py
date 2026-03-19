"""Repository for insights analysis basket persistence."""

import json
import sqlite3

from backend.database.connection import get_db_connection
from backend.schemas.insights import InsightsBasketItem


def save_insights_basket(
    user_id: int,
    *,
    items: list[InsightsBasketItem],
    conn: sqlite3.Connection | None = None,
) -> None:
    """Save or replace a user's synchronized insights basket."""
    close = conn is None
    if conn is None:
        conn = get_db_connection()

    try:
        serialized_items = json.dumps(
            [item.model_dump(by_alias=True, mode="json") for item in items],
            ensure_ascii=False,
        )
        conn.execute(
            """
            INSERT INTO insights_basket_state (
                user_id,
                basket_json
            ) VALUES (?, ?)
            ON CONFLICT(user_id) DO UPDATE SET
                basket_json = excluded.basket_json,
                updated_at = CURRENT_TIMESTAMP
            """,
            (user_id, serialized_items),
        )
        if close:
            conn.commit()
    finally:
        if close:
            conn.close()


def get_insights_basket(
    user_id: int,
    *,
    conn: sqlite3.Connection | None = None,
) -> list[InsightsBasketItem]:
    """Load a user's synchronized insights basket."""
    close = conn is None
    if conn is None:
        conn = get_db_connection()

    try:
        row = conn.execute(
            """
            SELECT basket_json
            FROM insights_basket_state
            WHERE user_id = ?
            """,
            (user_id,),
        ).fetchone()
        if row is None:
            return []

        try:
            raw_items = json.loads(row["basket_json"])
        except json.JSONDecodeError:
            return []
        if not isinstance(raw_items, list):
            return []

        result: list[InsightsBasketItem] = []
        for raw_item in raw_items:
            try:
                result.append(InsightsBasketItem.model_validate(raw_item))
            except ValueError:
                continue
        return result
    finally:
        if close:
            conn.close()
