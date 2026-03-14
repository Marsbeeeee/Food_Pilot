import os
import sqlite3
import unittest
from unittest.mock import patch

from backend.database.connection import get_db_connection
from backend.database.init_db import init_db
from backend.schemas.estimate import EstimateRequest, EstimateResult
from backend.services.chat_service import create_empty_session, send_message_in_session
from backend.services.estimate_service import create_estimate_response


class FoodLogServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = os.path.join(
            os.getcwd(),
            "backend",
            "database",
            "test_food_log_service.db",
        )
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db_patch = patch("backend.database.connection.db_path", self.db_path)
        self.db_patch.start()
        init_db()

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (email, password_hash, display_name)
                VALUES (?, ?, ?)
                """,
                ("owner@example.com", "hashed-password", "Owner"),
            )
            self.user_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO users (email, password_hash, display_name)
                VALUES (?, ?, ?)
                """,
                ("other@example.com", "hashed-password", "Other"),
            )
            self.other_user_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()

    def tearDown(self) -> None:
        self.db_patch.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_chat_estimate_result_creates_food_log_entry(self) -> None:
        session = create_empty_session(self.user_id)

        with patch(
            "backend.services.chat_service.estimate_meal",
            return_value=_build_estimate_result(),
        ):
            exchange = send_message_in_session(
                self.user_id,
                int(session["id"]),
                "chicken salad",
                profile_id=12,
            )

        self.assertIsNotNone(exchange)
        entries = _list_food_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source_type"], "chat_message")
        self.assertEqual(entries[0]["session_id"], int(session["id"]))
        self.assertEqual(entries[0]["source_message_id"], int(exchange["assistant_message"]["id"]))
        self.assertEqual(entries[0]["meal_description"], "chicken salad")
        self.assertEqual(entries[0]["total_calories"], "240 kcal")

    def test_estimate_api_creates_food_log_entry(self) -> None:
        request_model = EstimateRequest(query="chicken salad")

        with patch(
            "backend.services.estimate_service.estimate_meal",
            return_value=_build_estimate_result(),
        ):
            status_code, response = create_estimate_response(request_model, self.user_id)

        self.assertEqual(status_code, 200)
        self.assertTrue(response.success)
        entries = _list_food_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source_type"], "estimate_api")
        self.assertIsNone(entries[0]["session_id"])
        self.assertIsNone(entries[0]["source_message_id"])
        self.assertEqual(entries[0]["meal_description"], "chicken salad")
        self.assertEqual(entries[0]["result_title"], "Chicken salad")

    def test_estimate_api_creates_food_log_entry_with_session_id_when_linked(self) -> None:
        session = create_empty_session(self.user_id)
        request_model = EstimateRequest(
            query="chicken salad",
            sessionId=int(session["id"]),
        )

        with patch(
            "backend.services.estimate_service.estimate_meal",
            return_value=_build_estimate_result(),
        ):
            status_code, response = create_estimate_response(request_model, self.user_id)

        self.assertEqual(status_code, 200)
        self.assertTrue(response.success)
        entries = _list_food_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source_type"], "estimate_api")
        self.assertEqual(entries[0]["session_id"], int(session["id"]))
        self.assertIsNone(entries[0]["source_message_id"])

    def test_estimate_api_returns_404_when_session_id_is_not_owned_by_user(self) -> None:
        session = create_empty_session(self.other_user_id)
        request_model = EstimateRequest(
            query="chicken salad",
            sessionId=int(session["id"]),
        )

        with patch(
            "backend.services.estimate_service.estimate_meal",
            return_value=_build_estimate_result(),
        ):
            status_code, response = create_estimate_response(request_model, self.user_id)

        self.assertEqual(status_code, 404)
        self.assertFalse(response.success)
        self.assertIsNotNone(response.error)
        self.assertEqual(response.error.code, "SESSION_NOT_FOUND")
        self.assertEqual(len(_list_food_log_entries()), 0)

    def test_estimate_api_returns_500_when_food_log_insert_fails(self) -> None:
        request_model = EstimateRequest(query="chicken salad")

        with patch(
            "backend.services.estimate_service.estimate_meal",
            return_value=_build_estimate_result(),
        ), patch(
            "backend.services.estimate_service.create_food_log_from_estimate",
            side_effect=sqlite3.IntegrityError("food log insert failed"),
        ):
            status_code, response = create_estimate_response(request_model, self.user_id)

        self.assertEqual(status_code, 500)
        self.assertFalse(response.success)
        self.assertEqual(len(_list_food_log_entries()), 0)

    def test_init_db_backfills_existing_estimate_result_messages(self) -> None:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chat_sessions (user_id, title)
                VALUES (?, ?)
                """,
                (self.user_id, "Lunch"),
            )
            session_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO messages (
                    session_id,
                    user_id,
                    role,
                    message_type,
                    content,
                    result_title,
                    result_confidence,
                    result_description,
                    result_items_json,
                    result_total,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    self.user_id,
                    "assistant",
                    "estimate_result",
                    "A lighter dressing would reduce calories.",
                    "Chicken salad",
                    "high",
                    "Protein-forward salad with avocado.",
                    '[{"name":"Chicken","portion":"150g","energy":"240 kcal"}]',
                    "240 kcal",
                    "2026-03-13 12:00:00",
                ),
            )
            message_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()

        self.assertEqual(len(_list_food_log_entries()), 0)

        init_db()

        entries = _list_food_log_entries()
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]["source_message_id"], message_id)
        self.assertEqual(entries[0]["source_type"], "chat_message")
        self.assertEqual(entries[0]["meal_description"], "Chicken salad")
        self.assertEqual(entries[0]["created_at"], "2026-03-13 12:00:00")

    def test_init_db_adds_food_logs_table_to_existing_database_without_rebuild(self) -> None:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE food_logs")
            cursor.execute(
                """
                INSERT INTO chat_sessions (user_id, title)
                VALUES (?, ?)
                """,
                (self.user_id, "Legacy upgrade"),
            )
            session_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO messages (
                    session_id,
                    user_id,
                    role,
                    message_type,
                    content,
                    result_title,
                    result_confidence,
                    result_description,
                    result_items_json,
                    result_total,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    self.user_id,
                    "assistant",
                    "estimate_result",
                    "Legacy assistant suggestion",
                    "Legacy meal",
                    "medium",
                    "Legacy meal description.",
                    '[{"name":"Rice","portion":"1 bowl","energy":"230 kcal"}]',
                    "230 kcal",
                    "2026-03-14 08:30:00",
                ),
            )
            message_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()

        init_db()

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name = 'food_logs'
                """
            )
            table_row = cursor.fetchone()
            cursor.execute(
                """
                SELECT source_message_id, result_title, total_calories
                FROM food_logs
                WHERE source_message_id = ?
                """,
                (message_id,),
            )
            food_log_row = cursor.fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(table_row)
        self.assertIsNotNone(food_log_row)
        self.assertEqual(food_log_row["source_message_id"], message_id)
        self.assertEqual(food_log_row["result_title"], "Legacy meal")
        self.assertEqual(food_log_row["total_calories"], "230 kcal")

    def test_food_logs_table_has_expected_indexes_and_foreign_keys(self) -> None:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'index'
                AND tbl_name = 'food_logs'
                """
            )
            index_names = {row["name"] for row in cursor.fetchall()}

            cursor.execute("PRAGMA foreign_key_list(food_logs)")
            foreign_keys = {
                (row["from"], row["table"], row["to"], row["on_delete"])
                for row in cursor.fetchall()
            }
        finally:
            conn.close()

        self.assertTrue(
            {
                "idx_food_logs_user_id",
                "idx_food_logs_session_id",
                "idx_food_logs_logged_at",
                "idx_food_logs_user_logged_at",
                "idx_food_logs_source_message_id_unique",
            }.issubset(index_names)
        )
        self.assertEqual(
            foreign_keys,
            {
                ("user_id", "users", "id", "CASCADE"),
                ("session_id", "chat_sessions", "id", "SET NULL"),
                ("source_message_id", "messages", "id", "SET NULL"),
            },
        )

    def test_source_message_id_unique_index_blocks_duplicate_food_logs(self) -> None:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO chat_sessions (user_id, title)
                VALUES (?, ?)
                """,
                (self.user_id, "Lunch"),
            )
            session_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO messages (
                    session_id,
                    user_id,
                    role,
                    message_type,
                    content,
                    result_title,
                    result_confidence,
                    result_description,
                    result_items_json,
                    result_total
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    self.user_id,
                    "assistant",
                    "estimate_result",
                    "Assistant suggestion",
                    "Chicken salad",
                    "high",
                    "Protein-forward salad with avocado.",
                    '[{"name":"Chicken","portion":"150g","energy":"240 kcal"}]',
                    "240 kcal",
                ),
            )
            message_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO food_logs (
                    user_id,
                    session_id,
                    source_message_id,
                    meal_description,
                    logged_at,
                    result_title,
                    result_description,
                    total_calories,
                    ingredients_json,
                    source_type,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.user_id,
                    session_id,
                    message_id,
                    "chicken salad",
                    "2026-03-14 09:00:00",
                    "Chicken salad",
                    "Protein-forward salad with avocado.",
                    "240 kcal",
                    '[{"name":"Chicken","portion":"150g","energy":"240 kcal"}]',
                    "chat_message",
                    "2026-03-14 09:00:00",
                    "2026-03-14 09:00:00",
                ),
            )
            conn.commit()

            with self.assertRaises(sqlite3.IntegrityError):
                cursor.execute(
                    """
                    INSERT INTO food_logs (
                        user_id,
                        session_id,
                        source_message_id,
                        meal_description,
                        logged_at,
                        result_title,
                        result_description,
                        total_calories,
                        ingredients_json,
                        source_type,
                        created_at,
                        updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        self.user_id,
                        session_id,
                        message_id,
                        "same message duplicate",
                        "2026-03-14 09:01:00",
                        "Chicken salad duplicate",
                        "Duplicate entry should fail.",
                        "240 kcal",
                        '[{"name":"Chicken","portion":"150g","energy":"240 kcal"}]',
                        "chat_message",
                        "2026-03-14 09:01:00",
                        "2026-03-14 09:01:00",
                    ),
                )
                conn.commit()
        finally:
            conn.close()


def _build_estimate_result() -> EstimateResult:
    return EstimateResult(
        title="Chicken salad",
        description="Protein-forward salad with avocado.",
        confidence="high",
        items=[
            {
                "name": "Chicken",
                "portion": "150g",
                "energy": "240 kcal",
            }
        ],
        total_calories="240 kcal",
        suggestion="A lighter dressing would reduce calories.",
    )


def _list_food_log_entries() -> list[dict[str, object]]:
    conn = get_db_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            """
            SELECT
                id,
                source_type,
                session_id,
                source_message_id,
                meal_description,
                result_title,
                total_calories,
                created_at
            FROM food_logs
            ORDER BY id ASC
            """
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
