import os
import unittest
from datetime import date
from unittest.mock import patch

from backend.database.connection import get_db_connection
from backend.database.init_db import init_db
from backend.repositories.food_log_repository import (
    create_food_log,
    delete_food_log,
    get_food_log_by_id,
    list_food_logs_by_session,
    list_food_logs_by_user,
    list_food_logs_by_user_recent,
    save_food_log,
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
                created_at="2026-03-14 08:00:00",
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
                created_at="2026-03-14 09:00:00",
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
                created_at="2026-03-14 10:00:00",
            )

            session_logs = list_food_logs_by_session(conn, self.user_id, self.session_id)
            paged_logs = list_food_logs_by_user(conn, self.user_id, limit=2, offset=1)
            recent_logs = list_food_logs_by_user_recent(conn, self.user_id, limit=2)
        finally:
            conn.close()

        self.assertEqual([entry["result_title"] for entry in session_logs], ["Meal three", "Meal one"])
        self.assertEqual([entry["result_title"] for entry in paged_logs], ["Meal two", "Meal one"])
        self.assertEqual([entry["result_title"] for entry in recent_logs], ["Meal three", "Meal two"])

    def test_list_food_logs_orders_by_last_update_time(self) -> None:
        conn = get_db_connection()
        try:
            oldest = create_food_log(
                conn,
                self.user_id,
                source_type="chat_message",
                session_id=self.session_id,
                meal_description="meal one",
                result_title="Meal one",
                result_description="Description one",
                total_calories="100 kcal",
                ingredients=[],
                logged_at="2000-01-01 08:00:00",
                created_at="2000-01-01 08:00:00",
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
                logged_at="2000-01-01 09:00:00",
                created_at="2000-01-01 09:00:00",
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
                logged_at="2000-01-01 10:00:00",
                created_at="2000-01-01 10:00:00",
            )

            conn.execute(
                """
                UPDATE food_logs
                SET result_description = ?
                WHERE id = ?
                """,
                ("Updated after re-save", int(oldest["id"])),
            )
            conn.commit()

            all_logs = list_food_logs_by_user(conn, self.user_id)
            session_logs = list_food_logs_by_session(conn, self.user_id, self.session_id)
        finally:
            conn.close()

        self.assertEqual(
            [entry["result_title"] for entry in all_logs],
            ["Meal one", "Meal three", "Meal two"],
        )
        self.assertEqual(
            [entry["result_title"] for entry in session_logs],
            ["Meal one", "Meal three"],
        )

    def test_list_food_logs_date_filters_use_last_save_time(self) -> None:
        conn = get_db_connection()
        try:
            resaved = create_food_log(
                conn,
                self.user_id,
                source_type="estimate_api",
                meal_description="meal one",
                result_title="Meal one",
                result_description="Description one",
                total_calories="100 kcal",
                ingredients=[],
                logged_at="2000-01-01 08:00:00",
                created_at="2000-01-01 08:00:00",
            )
            create_food_log(
                conn,
                self.user_id,
                source_type="estimate_api",
                meal_description="meal two",
                result_title="Meal two",
                result_description="Description two",
                total_calories="200 kcal",
                ingredients=[],
                logged_at="2000-01-02 08:00:00",
                created_at="2000-01-02 08:00:00",
            )

            conn.execute(
                """
                UPDATE food_logs
                SET updated_at = ?
                WHERE id = ?
                """,
                ("2026-03-15 09:00:00", int(resaved["id"])),
            )
            conn.commit()

            filtered_logs = list_food_logs_by_user(
                conn,
                self.user_id,
                date_from=date(2026, 3, 15),
                date_to=date(2026, 3, 15),
            )
        finally:
            conn.close()

        self.assertEqual([entry["result_title"] for entry in filtered_logs], ["Meal one"])

    def test_save_food_log_overwrites_existing_chat_message_entry(self) -> None:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
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
                    self.session_id,
                    self.user_id,
                    "assistant",
                    "estimate_result",
                    "Assistant suggestion",
                    "Chicken Salad",
                    "high",
                    "First description",
                    '[{"name":"Chicken","portion":"150g","energy":"240 kcal"}]',
                    "240 kcal",
                ),
            )
            first_source_message_id = cursor.lastrowid
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
                    self.second_session_id,
                    self.user_id,
                    "assistant",
                    "estimate_result",
                    "Assistant suggestion updated",
                    "Chicken Salad",
                    "high",
                    "Updated description",
                    '[{"name":"Chicken","portion":"150g","energy":"260 kcal"}]',
                    "260 kcal",
                ),
            )
            second_source_message_id = cursor.lastrowid
            conn.commit()

            first_save = save_food_log(
                conn,
                self.user_id,
                source_type="chat_message",
                session_id=self.session_id,
                source_message_id=first_source_message_id,
                meal_description=" Chicken   Salad ",
                result_title="Chicken Salad",
                result_description="First description",
                total_calories="240 kcal",
                ingredients=[],
                created_at="2000-01-01 09:00:00",
            )
            second_save = save_food_log(
                conn,
                self.user_id,
                source_type="chat_message",
                session_id=self.second_session_id,
                source_message_id=second_source_message_id,
                meal_description="chicken salad",
                result_title="Chicken Salad Updated",
                result_description="Updated description",
                total_calories="260 kcal",
                ingredients=[],
            )

            cursor.execute("SELECT COUNT(*) AS total FROM food_logs WHERE user_id = ?", (self.user_id,))
            total = cursor.fetchone()["total"]
        finally:
            conn.close()

        self.assertEqual(total, 1)
        self.assertEqual(first_save["id"], second_save["id"])
        self.assertEqual(second_save["created_at"], "2000-01-01 09:00:00")
        self.assertNotEqual(second_save["updated_at"], "2000-01-01 09:00:00")
        self.assertEqual(second_save["meal_description"], "chicken salad")
        self.assertEqual(second_save["result_title"], "Chicken Salad Updated")
        self.assertEqual(second_save["total_calories"], "260 kcal")
        self.assertEqual(second_save["session_id"], self.second_session_id)
        self.assertEqual(second_save["source_message_id"], second_source_message_id)

    def test_list_food_logs_excludes_soft_deleted_entries(self) -> None:
        conn = get_db_connection()
        try:
            created = create_food_log(
                conn,
                self.user_id,
                source_type="estimate_api",
                meal_description="chicken salad",
                result_title="Chicken Salad",
                result_description="Description",
                total_calories="240 kcal",
                ingredients=[],
                created_at="2026-03-14 09:00:00",
            )
            conn.execute(
                """
                UPDATE food_logs
                SET deleted_at = ?
                WHERE id = ?
                """,
                ("2026-03-15 09:00:00", int(created["id"])),
            )
            conn.commit()

            listed = list_food_logs_by_user(conn, self.user_id)
            fetched = get_food_log_by_id(conn, int(created["id"]), self.user_id)
        finally:
            conn.close()

        self.assertEqual(listed, [])
        self.assertIsNone(fetched)

    def test_delete_food_log_soft_deletes_entry_and_hides_it(self) -> None:
        conn = get_db_connection()
        try:
            created = create_food_log(
                conn,
                self.user_id,
                source_type="estimate_api",
                meal_description="salmon bowl",
                result_title="Salmon Bowl",
                result_description="Description",
                total_calories="520 kcal",
                ingredients=[],
                created_at="2026-03-14 09:00:00",
            )

            deleted = delete_food_log(conn, int(created["id"]), self.user_id)
            deleted_again = delete_food_log(conn, int(created["id"]), self.user_id)
            row = conn.execute(
                """
                SELECT deleted_at
                FROM food_logs
                WHERE id = ?
                """,
                (int(created["id"]),),
            ).fetchone()
            listed = list_food_logs_by_user(conn, self.user_id)
            fetched = get_food_log_by_id(conn, int(created["id"]), self.user_id)
        finally:
            conn.close()

        self.assertTrue(deleted)
        self.assertFalse(deleted_again)
        self.assertIsNotNone(row["deleted_at"])
        self.assertEqual(listed, [])
        self.assertIsNone(fetched)

    def test_save_food_log_restores_soft_deleted_entry_and_preserves_created_at(self) -> None:
        conn = get_db_connection()
        try:
            created = create_food_log(
                conn,
                self.user_id,
                source_type="estimate_api",
                meal_description=" Chicken   Salad ",
                result_title="Chicken Salad",
                result_description="First description",
                total_calories="240 kcal",
                ingredients=[],
                created_at="2026-03-14 09:00:00",
            )
            conn.execute(
                """
                UPDATE food_logs
                SET deleted_at = ?
                WHERE id = ?
                """,
                ("2026-03-15 09:00:00", int(created["id"])),
            )
            conn.commit()

            restored = save_food_log(
                conn,
                self.user_id,
                source_type="estimate_api",
                meal_description="chicken salad",
                result_title="Chicken Salad Updated",
                result_description="Updated description",
                total_calories="260 kcal",
                ingredients=[],
            )
            row = conn.execute(
                """
                SELECT created_at, updated_at, deleted_at, result_title, total_calories
                FROM food_logs
                WHERE id = ?
                """,
                (int(created["id"]),),
            ).fetchone()
            total = conn.execute(
                """
                SELECT COUNT(*) AS total
                FROM food_logs
                WHERE user_id = ?
                """,
                (self.user_id,),
            ).fetchone()["total"]
        finally:
            conn.close()

        self.assertEqual(restored["id"], created["id"])
        self.assertEqual(restored["result_title"], "Chicken Salad Updated")
        self.assertEqual(restored["total_calories"], "260 kcal")
        self.assertEqual(total, 1)
        self.assertEqual(row["created_at"], "2026-03-14 09:00:00")
        self.assertNotEqual(row["updated_at"], "2026-03-14 09:00:00")
        self.assertIsNone(row["deleted_at"])
        self.assertEqual(row["result_title"], "Chicken Salad Updated")

    def test_init_db_backfills_and_dedupes_normalized_query(self) -> None:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO food_logs (
                    user_id,
                    session_id,
                    source_message_id,
                    meal_description,
                    normalized_query,
                    logged_at,
                    result_title,
                    result_description,
                    total_calories,
                    ingredients_json,
                    source_type,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.user_id,
                    self.session_id,
                    None,
                    " Chicken   Salad ",
                    "",
                    "2026-03-14 09:00:00",
                    "Chicken Salad",
                    "First description",
                    "240 kcal",
                    "[]",
                    "estimate_api",
                    "2026-03-14 09:00:00",
                    "2026-03-14 09:00:00",
                ),
            )
            cursor.execute(
                """
                INSERT INTO food_logs (
                    user_id,
                    session_id,
                    source_message_id,
                    meal_description,
                    normalized_query,
                    logged_at,
                    result_title,
                    result_description,
                    total_calories,
                    ingredients_json,
                    source_type,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.user_id,
                    self.second_session_id,
                    None,
                    "chicken salad",
                    "",
                    "2026-03-14 10:00:00",
                    "Chicken Salad Newer",
                    "Updated description",
                    "260 kcal",
                    "[]",
                    "estimate_api",
                    "2026-03-14 10:00:00",
                    "2026-03-14 10:00:00",
                ),
            )
            conn.commit()
        finally:
            conn.close()

        init_db()

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT id, meal_description, normalized_query, result_title
                FROM food_logs
                WHERE user_id = ?
                ORDER BY id ASC
                """,
                (self.user_id,),
            )
            rows = cursor.fetchall()
        finally:
            conn.close()

        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["meal_description"], "chicken salad")
        self.assertEqual(rows[0]["normalized_query"], "chicken salad")
        self.assertEqual(rows[0]["result_title"], "Chicken Salad Newer")

    def test_init_db_dedupe_prefers_active_row_over_soft_deleted_duplicate(self) -> None:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO food_logs (
                    user_id,
                    session_id,
                    source_message_id,
                    meal_description,
                    normalized_query,
                    logged_at,
                    result_title,
                    result_description,
                    total_calories,
                    ingredients_json,
                    source_type,
                    created_at,
                    updated_at,
                    deleted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.user_id,
                    self.session_id,
                    None,
                    "Chicken Salad",
                    "",
                    "2026-03-14 09:00:00",
                    "Active favorite",
                    "Should remain after dedupe.",
                    "240 kcal",
                    "[]",
                    "estimate_api",
                    "2026-03-14 09:00:00",
                    "2026-03-14 09:00:00",
                    None,
                ),
            )
            cursor.execute(
                """
                INSERT INTO food_logs (
                    user_id,
                    session_id,
                    source_message_id,
                    meal_description,
                    normalized_query,
                    logged_at,
                    result_title,
                    result_description,
                    total_calories,
                    ingredients_json,
                    source_type,
                    created_at,
                    updated_at,
                    deleted_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    self.user_id,
                    self.second_session_id,
                    None,
                    " chicken   salad ",
                    "",
                    "2026-03-14 10:00:00",
                    "Soft deleted newer row",
                    "Should be discarded during dedupe.",
                    "260 kcal",
                    "[]",
                    "estimate_api",
                    "2026-03-14 10:00:00",
                    "2026-03-14 10:00:00",
                    "2026-03-14 11:00:00",
                ),
            )
            conn.commit()
        finally:
            conn.close()

        init_db()

        conn = get_db_connection()
        try:
            row = conn.execute(
                """
                SELECT meal_description, normalized_query, result_title, deleted_at
                FROM food_logs
                WHERE user_id = ?
                """,
                (self.user_id,),
            ).fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(row)
        self.assertEqual(row["meal_description"], "Chicken Salad")
        self.assertEqual(row["normalized_query"], "chicken salad")
        self.assertEqual(row["result_title"], "Active favorite")
        self.assertIsNone(row["deleted_at"])


if __name__ == "__main__":
    unittest.main()
