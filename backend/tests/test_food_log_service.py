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

    def test_chat_estimate_result_does_not_create_food_log_entry(self) -> None:
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
        self.assertEqual(len(entries), 0)

    def test_estimate_api_does_not_create_food_log_entry(self) -> None:
        request_model = EstimateRequest(query="chicken salad")

        with patch(
            "backend.services.estimate_service.estimate_meal",
            return_value=_build_estimate_result(),
        ):
            status_code, response = create_estimate_response(request_model, self.user_id)

        self.assertEqual(status_code, 200)
        self.assertTrue(response.success)
        self.assertIsNone(response.food_log_id)
        self.assertEqual(response.save_status, "not_saved")
        entries = _list_food_log_entries()
        self.assertEqual(len(entries), 0)

    def test_estimate_api_ignores_session_id_for_food_log_until_save(self) -> None:
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
        self.assertIsNone(response.food_log_id)
        self.assertEqual(response.save_status, "not_saved")
        self.assertEqual(len(_list_food_log_entries()), 0)

    def test_estimate_api_does_not_require_owned_session_id_until_save(self) -> None:
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

        self.assertEqual(status_code, 200)
        self.assertTrue(response.success)
        self.assertIsNone(response.food_log_id)
        self.assertEqual(response.save_status, "not_saved")
        self.assertEqual(len(_list_food_log_entries()), 0)

    def test_init_db_does_not_backfill_existing_estimate_result_messages(self) -> None:
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

        self.assertEqual(len(_list_food_log_entries()), 0)

    def test_init_db_adds_food_logs_table_to_existing_database_without_backfill(self) -> None:
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
                SELECT COUNT(*) AS total
                FROM food_logs
                """,
            )
            food_log_row = cursor.fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(table_row)
        self.assertIsNotNone(food_log_row)
        self.assertEqual(food_log_row["total"], 0)

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
                "idx_food_logs_user_meal_occurred_at",
                "idx_food_logs_user_updated_at",
                "idx_food_logs_source_message_id",
                "idx_food_logs_user_idempotency_key_unique",
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

    def test_user_idempotency_key_unique_index_blocks_duplicate_food_logs(self) -> None:
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
                    normalized_query,
                    result_title,
                    result_description,
                    total_calories,
                    ingredients_json,
                    source_type,
                    idempotency_key
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.user_id,
                    session_id,
                    message_id,
                    " Chicken   Salad ",
                    "chicken salad",
                    "Chicken salad",
                    "Protein-forward salad with avocado.",
                    "240 kcal",
                    '[{"name":"Chicken","portion":"150g","energy":"240 kcal"}]',
                    "chat_message",
                    "chat_message:123",
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
                        normalized_query,
                        result_title,
                        result_description,
                        total_calories,
                        ingredients_json,
                        source_type,
                        idempotency_key
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        self.user_id,
                        session_id,
                        message_id,
                        "chicken salad",
                        "chicken salad",
                        "Chicken salad duplicate",
                        "Duplicate entry should fail.",
                        "240 kcal",
                        '[{"name":"Chicken","portion":"150g","energy":"240 kcal"}]',
                        "chat_message",
                        "chat_message:123",
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
