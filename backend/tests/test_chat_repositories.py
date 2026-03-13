import os
import sqlite3
import unittest
from unittest.mock import patch

from backend.database.connection import get_db_connection
from backend.database.init_db import init_db
from backend.repositories.chat_session_repository import (
    create_session,
    delete_session,
    get_session_by_id,
    list_sessions_by_user,
    touch_session_activity,
    update_session_title,
)
from backend.repositories.message_repository import (
    create_message,
    delete_messages_by_session,
    list_messages_by_session,
)


class ChatRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = os.path.join(
            os.getcwd(),
            "backend",
            "database",
            "test_chat_repositories.db",
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

    def test_chat_session_repository_round_trip(self) -> None:
        conn = get_db_connection()
        try:
            created = create_session(conn, self.user_id, "First session")
            fetched = get_session_by_id(conn, created["id"], self.user_id)
            listed = list_sessions_by_user(conn, self.user_id)
        finally:
            conn.close()

        self.assertEqual(created["title"], "First session")
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched["id"], created["id"])
        self.assertEqual(len(listed), 1)
        self.assertEqual(listed[0]["id"], created["id"])

    def test_update_and_delete_session_are_user_scoped(self) -> None:
        conn = get_db_connection()
        try:
            created = create_session(conn, self.user_id, "Original title")

            self.assertIsNone(
                update_session_title(
                    conn,
                    created["id"],
                    self.other_user_id,
                    "Wrong owner edit",
                )
            )

            updated = update_session_title(
                conn,
                created["id"],
                self.user_id,
                "Renamed session",
            )
            deleted_by_other_user = delete_session(conn, created["id"], self.other_user_id)
            deleted_by_owner = delete_session(conn, created["id"], self.user_id)
        finally:
            conn.close()

        self.assertIsNotNone(updated)
        self.assertEqual(updated["title"], "Renamed session")
        self.assertFalse(deleted_by_other_user)
        self.assertTrue(deleted_by_owner)

    def test_touch_session_activity_updates_sort_order(self) -> None:
        conn = get_db_connection()
        try:
            older = create_session(conn, self.user_id, "Older session")
            newer = create_session(conn, self.user_id, "Newer session")

            touched = touch_session_activity(conn, older["id"], "2099-01-01 00:00:00")
            listed = list_sessions_by_user(conn, self.user_id)
        finally:
            conn.close()

        self.assertTrue(touched)
        self.assertEqual(listed[0]["id"], older["id"])
        self.assertEqual(listed[1]["id"], newer["id"])

    def test_message_repository_creates_and_lists_user_scoped_messages(self) -> None:
        conn = get_db_connection()
        try:
            session = create_session(conn, self.user_id, "Meal log")
            create_message(
                conn,
                session["id"],
                self.user_id,
                "user",
                "text",
                content="Chicken salad",
            )
            created_result = create_message(
                conn,
                session["id"],
                self.user_id,
                "assistant",
                "estimate_result",
                content="A lighter dressing would reduce calories.",
                result_title="Chicken salad",
                result_confidence="high",
                result_description="Protein-forward salad with avocado.",
                result_items_json='[{"name":"Chicken","portion":"150g","energy":"240 kcal"}]',
                result_total="240 kcal",
            )
            listed = list_messages_by_session(conn, session["id"], self.user_id)
            listed_for_other_user = list_messages_by_session(conn, session["id"], self.other_user_id)
        finally:
            conn.close()

        self.assertEqual(created_result["message_type"], "estimate_result")
        self.assertEqual(len(listed), 2)
        self.assertEqual(listed[1]["result_total"], "240 kcal")
        self.assertEqual(listed_for_other_user, [])

    def test_delete_messages_by_session_is_user_scoped(self) -> None:
        conn = get_db_connection()
        try:
            session = create_session(conn, self.user_id, "Delete messages")
            create_message(
                conn,
                session["id"],
                self.user_id,
                "user",
                "text",
                content="Greek yogurt",
            )
            create_message(
                conn,
                session["id"],
                self.user_id,
                "assistant",
                "text",
                content="Estimated at 120 kcal.",
            )

            deleted_by_other_user = delete_messages_by_session(
                conn,
                session["id"],
                self.other_user_id,
            )
            deleted_by_owner = delete_messages_by_session(
                conn,
                session["id"],
                self.user_id,
            )
            remaining = list_messages_by_session(conn, session["id"], self.user_id)
        finally:
            conn.close()

        self.assertEqual(deleted_by_other_user, 0)
        self.assertEqual(deleted_by_owner, 2)
        self.assertEqual(remaining, [])

    def test_create_message_respects_database_constraints(self) -> None:
        conn = get_db_connection()
        try:
            session = create_session(conn, self.user_id, "Invalid message")

            with self.assertRaises(sqlite3.IntegrityError):
                create_message(
                    conn,
                    session["id"],
                    self.user_id,
                    "assistant",
                    "estimate_result",
                    result_title="Broken result",
                    result_confidence="high",
                    result_description="Missing items and total.",
                )
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
