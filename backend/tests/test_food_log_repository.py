import os
import unittest
from unittest.mock import patch

from backend.database.connection import get_db_connection
from backend.database.init_db import init_db
from backend.repositories.food_log_repository import (
    create_food_log,
    get_food_log_by_id,
    list_food_logs_by_session,
    list_food_logs_by_user,
    list_food_logs_by_user_recent,
)


class FoodLogRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = os.path.join(
            os.getcwd(),
            "backend",
            "database",
            "test_food_log_repository.db",
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
                INSERT INTO chat_sessions (user_id, title)
                VALUES (?, ?)
                """,
                (self.user_id, "Session A"),
            )
            self.session_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO chat_sessions (user_id, title)
                VALUES (?, ?)
                """,
                (self.user_id, "Session B"),
            )
            self.second_session_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()

    def tearDown(self) -> None:
        self.db_patch.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_create_food_log_serializes_ingredients_and_returns_dict(self) -> None:
        conn = get_db_connection()
        try:
            created = create_food_log(
                conn,
                self.user_id,
                source_type="chat_message",
                session_id=self.session_id,
                meal_description="chicken salad",
                result_title="Chicken salad",
                result_description="Protein-forward salad.",
                total_calories="240 kcal",
                ingredients=[
                    {"name": "Chicken", "portion": "150g", "energy": "240 kcal"},
                ],
                logged_at="2026-03-14 10:00:00",
            )
        finally:
            conn.close()

        self.assertEqual(created["user_id"], self.user_id)
        self.assertEqual(created["session_id"], self.session_id)
        self.assertEqual(
            created["ingredients_json"],
            '[{"name": "Chicken", "portion": "150g", "energy": "240 kcal"}]',
        )

    def test_get_food_log_by_id_is_user_scoped(self) -> None:
        conn = get_db_connection()
        try:
            created = create_food_log(
                conn,
                self.user_id,
                source_type="chat_message",
                session_id=self.session_id,
                meal_description="oatmeal",
                result_title="Oatmeal bowl",
                result_description="Balanced breakfast.",
                total_calories="320 kcal",
                ingredients='[{"name":"Oats","portion":"60g","energy":"230 kcal"}]',
            )
            fetched = get_food_log_by_id(conn, int(created["id"]), self.user_id)
            missing = get_food_log_by_id(conn, int(created["id"]), self.user_id + 1)
        finally:
            conn.close()

        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["id"], created["id"])
        self.assertIsNone(missing)

    def test_list_food_logs_by_session_and_recent_support_limit_offset(self) -> None:
        conn = get_db_connection()
        try:
            create_food_log(
                conn,
                self.user_id,
                source_type="chat_message",
                session_id=self.session_id,
                meal_description="meal one",
                result_title="Meal one",
                result_description="Description one",
                total_calories="100 kcal",
                ingredients=[],
                logged_at="2026-03-14 08:00:00",
            )
            create_food_log(
                conn,
                self.user_id,
                source_type="chat_message",
                session_id=self.second_session_id,
                meal_description="meal two",
                result_title="Meal two",
                result_description="Description two",
                total_calories="200 kcal",
                ingredients=[],
                logged_at="2026-03-14 09:00:00",
            )
            create_food_log(
                conn,
                self.user_id,
                source_type="chat_message",
                session_id=self.session_id,
                meal_description="meal three",
                result_title="Meal three",
                result_description="Description three",
                total_calories="300 kcal",
                ingredients=[],
                logged_at="2026-03-14 10:00:00",
            )

            session_logs = list_food_logs_by_session(conn, self.user_id, self.session_id)
            paged_logs = list_food_logs_by_user(conn, self.user_id, limit=2, offset=1)
            recent_logs = list_food_logs_by_user_recent(conn, self.user_id, limit=2)
        finally:
            conn.close()

        self.assertEqual([entry["result_title"] for entry in session_logs], ["Meal three", "Meal one"])
        self.assertEqual([entry["result_title"] for entry in paged_logs], ["Meal two", "Meal one"])
        self.assertEqual([entry["result_title"] for entry in recent_logs], ["Meal three", "Meal two"])


if __name__ == "__main__":
    unittest.main()
