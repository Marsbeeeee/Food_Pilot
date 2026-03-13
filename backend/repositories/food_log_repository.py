import sqlite3


def create_food_log_entry(
    conn: sqlite3.Connection,
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
) -> dict[str, object]:
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO food_logs (
            user_id,
            session_id,
            source_message_id,
            meal_description,
            logged_at,
            result_title,
            result_confidence,
            result_description,
            total_calories,
            ingredients_json,
            source_type,
            assistant_suggestion,
            created_at,
            updated_at
        ) VALUES (?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), ?, ?, ?, ?, ?, ?, ?, COALESCE(?, CURRENT_TIMESTAMP), COALESCE(?, CURRENT_TIMESTAMP))
        """,
        (
            user_id,
            session_id,
            source_message_id,
            meal_description,
            logged_at,
            result_title,
            result_confidence,
            result_description,
            total_calories,
            ingredients_json,
            source_type,
            assistant_suggestion,
            created_at,
            created_at,
        ),
    )
    conn.commit()
    return get_food_log_entry_by_id(conn, cursor.lastrowid, user_id)


def list_food_log_entries_by_user(
    conn: sqlite3.Connection,
    user_id: int,
) -> list[dict[str, object]]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id,
            user_id,
            session_id,
            source_message_id,
            meal_description,
            logged_at,
            result_title,
            result_confidence,
            result_description,
            total_calories,
            ingredients_json,
            source_type,
            assistant_suggestion,
            created_at,
            updated_at
        FROM food_logs
        WHERE user_id = ?
        ORDER BY logged_at DESC, id DESC
        """,
        (user_id,),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_food_log_entry_by_id(
    conn: sqlite3.Connection,
    entry_id: int,
    user_id: int,
) -> dict[str, object]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id,
            user_id,
            session_id,
            source_message_id,
            meal_description,
            logged_at,
            result_title,
            result_confidence,
            result_description,
            total_calories,
            ingredients_json,
            source_type,
            assistant_suggestion,
            created_at,
            updated_at
        FROM food_logs
        WHERE id = ? AND user_id = ?
        """,
        (entry_id, user_id),
    )
    row = cursor.fetchone()
    if row is None:
        raise LookupError("food log entry not found after insert")
    return dict(row)
