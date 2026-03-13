import os
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
        self.assertEqual(entries[0]["message_id"], int(exchange["assistant_message"]["id"]))
        self.assertEqual(entries[0]["total"], "240 kcal")

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
        self.assertIsNone(entries[0]["message_id"])
        self.assertEqual(entries[0]["title"], "Chicken salad")

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
        self.assertEqual(entries[0]["message_id"], message_id)
        self.assertEqual(entries[0]["source_type"], "chat_message")
        self.assertEqual(entries[0]["created_at"], "2026-03-13 12:00:00")


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
                message_id,
                title,
                total,
                created_at
            FROM food_log_entries
            ORDER BY id ASC
            """
        )
        return [dict(row) for row in cursor.fetchall()]
    finally:
        conn.close()


if __name__ == "__main__":
    unittest.main()
