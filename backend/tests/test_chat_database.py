import os
import sqlite3
import unittest
from unittest.mock import patch

from backend.database.connection import get_db_connection
from backend.database.init_db import init_db


class ChatDatabaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = os.path.join(
            os.getcwd(),
            "backend",
            "database",
            "test_chat_database.db",
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
            conn.commit()
            user_id = cursor.lastrowid
        finally:
            conn.close()

        self.user_id = user_id

    def tearDown(self) -> None:
        self.db_patch.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_init_db_creates_chat_tables_with_expected_columns(self) -> None:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(chat_sessions)")
            chat_session_columns = {row["name"] for row in cursor.fetchall()}

            cursor.execute("PRAGMA table_info(messages)")
            message_columns = {row["name"] for row in cursor.fetchall()}
        finally:
            conn.close()

        self.assertEqual(
            chat_session_columns,
            {
                "id",
                "user_id",
                "title",
                "created_at",
                "updated_at",
                "last_message_at",
                "deleted_at",
            },
        )
        self.assertEqual(
            message_columns,
            {
                "id",
                "session_id",
                "user_id",
                "role",
                "message_type",
                "content",
                "result_title",
                "result_confidence",
                "result_description",
                "result_items_json",
                "result_total",
                "created_at",
            },
        )

    def test_init_db_creates_chat_indexes(self) -> None:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'index'
                AND tbl_name IN ('chat_sessions', 'messages')
                """
            )
            index_names = {row["name"] for row in cursor.fetchall()}
        finally:
            conn.close()

        self.assertTrue(
            {
                "idx_chat_sessions_user_last_message_at",
                "idx_messages_session_id_id",
                "idx_messages_user_created_at",
            }.issubset(index_names)
        )

    def test_message_constraints_accept_supported_shapes(self) -> None:
        conn = get_db_connection()
        try:
            session_id = _insert_session(conn, self.user_id, "Lunch estimate")
            _insert_text_message(
                conn,
                session_id,
                self.user_id,
                role="user",
                content="Chicken salad with avocado",
            )
            _insert_text_message(
                conn,
                session_id,
                self.user_id,
                role="assistant",
                content="Let me estimate that meal for you.",
            )
            _insert_estimate_result_message(conn, session_id, self.user_id)

            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM messages WHERE session_id = ?", (session_id,))
            total = cursor.fetchone()["total"]
        finally:
            conn.close()

        self.assertEqual(total, 3)

    def test_invalid_session_title_and_message_shapes_are_rejected(self) -> None:
        conn = get_db_connection()
        try:
            with self.assertRaises(sqlite3.IntegrityError):
                _insert_session(conn, self.user_id, "   ")

            session_id = _insert_session(conn, self.user_id, "Dinner")

            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO messages (
                        session_id,
                        user_id,
                        role,
                        message_type,
                        result_title,
                        result_confidence,
                        result_description,
                        result_items_json,
                        result_total
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        session_id,
                        self.user_id,
                        "user",
                        "estimate_result",
                        "Dinner",
                        "high",
                        "Estimated calories",
                        '[{"name":"Rice","portion":"1 bowl","energy":"230 kcal"}]',
                        "230 kcal",
                    ),
                )
                conn.commit()

            with self.assertRaises(sqlite3.IntegrityError):
                conn.execute(
                    """
                    INSERT INTO messages (
                        session_id,
                        user_id,
                        role,
                        message_type,
                        content
                    ) VALUES (?, ?, ?, ?, ?)
                    """,
                    (session_id, self.user_id, "assistant", "text", "   "),
                )
                conn.commit()
        finally:
            conn.close()

    def test_inserting_message_updates_session_last_message_at(self) -> None:
        conn = get_db_connection()
        try:
            session_id = _insert_session(conn, self.user_id, "Breakfast")
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO messages (
                    session_id,
                    user_id,
                    role,
                    message_type,
                    content,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    self.user_id,
                    "user",
                    "text",
                    "Oatmeal and berries",
                    "2026-03-13 09:30:00",
                ),
            )
            conn.commit()

            cursor.execute(
                "SELECT last_message_at FROM chat_sessions WHERE id = ?",
                (session_id,),
            )
            last_message_at = cursor.fetchone()["last_message_at"]
        finally:
            conn.close()

        self.assertEqual(last_message_at, "2026-03-13 09:30:00")

    def test_deleting_user_cascades_sessions_and_messages(self) -> None:
        conn = get_db_connection()
        try:
            session_id = _insert_session(conn, self.user_id, "Snack")
            _insert_text_message(
                conn,
                session_id,
                self.user_id,
                role="user",
                content="Greek yogurt",
            )

            conn.execute("DELETE FROM users WHERE id = ?", (self.user_id,))
            conn.commit()

            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM chat_sessions")
            session_total = cursor.fetchone()["total"]
            cursor.execute("SELECT COUNT(*) AS total FROM messages")
            message_total = cursor.fetchone()["total"]
        finally:
            conn.close()

        self.assertEqual(session_total, 0)
        self.assertEqual(message_total, 0)


def _insert_session(conn: sqlite3.Connection, user_id: int, title: str) -> int:
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO chat_sessions (user_id, title)
        VALUES (?, ?)
        """,
        (user_id, title),
    )
    conn.commit()
    return cursor.lastrowid


def _insert_text_message(
    conn: sqlite3.Connection,
    session_id: int,
    user_id: int,
    *,
    role: str,
    content: str,
) -> int:
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO messages (
            session_id,
            user_id,
            role,
            message_type,
            content
        ) VALUES (?, ?, ?, ?, ?)
        """,
        (session_id, user_id, role, "text", content),
    )
    conn.commit()
    return cursor.lastrowid


def _insert_estimate_result_message(
    conn: sqlite3.Connection,
    session_id: int,
    user_id: int,
) -> int:
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
            session_id,
            user_id,
            "assistant",
            "estimate_result",
            "A lighter dressing would reduce calories.",
            "Chicken salad",
            "high",
            "Protein-forward salad with avocado.",
            '[{"name":"Chicken","portion":"150g","energy":"240 kcal"}]',
            "240 kcal",
        ),
    )
    conn.commit()
    return cursor.lastrowid


if __name__ == "__main__":
    unittest.main()
