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
                "payload_json",
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
                "idx_chat_sessions_user_id",
                "idx_chat_sessions_last_message_at",
                "idx_chat_sessions_user_last_message_at",
                "idx_messages_session_id",
                "idx_messages_user_id",
                "idx_messages_session_id_id",
                "idx_messages_user_created_at",
            }.issubset(index_names)
        )

    def test_init_db_can_run_multiple_times_on_same_database(self) -> None:
        init_db()
        init_db()

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table'
                AND name IN ('chat_sessions', 'messages')
                """
            )
            table_names = {row["name"] for row in cursor.fetchall()}
        finally:
            conn.close()

        self.assertEqual(table_names, {"chat_sessions", "messages"})

    def test_init_db_migrates_legacy_chat_sessions_table(self) -> None:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("DROP TABLE messages")
            cursor.execute("DROP TABLE chat_sessions")
            cursor.execute(
                """
                CREATE TABLE chat_sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    title TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CHECK (length(trim(title)) BETWEEN 1 AND 120)
                );
                """
            )
            cursor.execute(
                """
                INSERT INTO chat_sessions (
                    user_id,
                    title,
                    created_at,
                    updated_at
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    self.user_id,
                    "Legacy session",
                    "2026-03-12 08:00:00",
                    "2026-03-12 09:00:00",
                ),
            )
            conn.commit()
        finally:
            conn.close()

        init_db()

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(chat_sessions)")
            chat_session_columns = {row["name"] for row in cursor.fetchall()}
            cursor.execute(
                """
                SELECT last_message_at, deleted_at
                FROM chat_sessions
                WHERE title = ?
                """,
                ("Legacy session",),
            )
            session_row = cursor.fetchone()
        finally:
            conn.close()

        self.assertIn("last_message_at", chat_session_columns)
        self.assertIn("deleted_at", chat_session_columns)
        self.assertEqual(session_row["last_message_at"], "2026-03-12 09:00:00")
        self.assertIsNone(session_row["deleted_at"])

    def test_init_db_migrates_legacy_messages_table(self) -> None:
        conn = get_db_connection()
        try:
            session_id = _insert_session(conn, self.user_id, "Message migration")
            cursor = conn.cursor()
            cursor.execute("DROP TABLE messages")
            cursor.execute(
                """
                CREATE TABLE messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    role TEXT NOT NULL,
                    content TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );
                """
            )
            cursor.execute(
                """
                INSERT INTO messages (
                    session_id,
                    role,
                    content,
                    created_at
                ) VALUES (?, ?, ?, ?)
                """,
                (
                    session_id,
                    "user",
                    "Legacy message",
                    "2026-03-13 10:15:00",
                ),
            )
            conn.commit()
        finally:
            conn.close()

        init_db()

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(messages)")
            message_columns = {row["name"] for row in cursor.fetchall()}
            cursor.execute(
                """
                SELECT user_id, message_type
                FROM messages
                WHERE content = ?
                """,
                ("Legacy message",),
            )
            message_row = cursor.fetchone()
        finally:
            conn.close()

        self.assertTrue(
            {
                "user_id",
                "message_type",
                "result_title",
                "result_confidence",
                "result_description",
                "result_items_json",
                "result_total",
            }.issubset(message_columns)
        )
        self.assertEqual(message_row["user_id"], self.user_id)
        self.assertEqual(message_row["message_type"], "text")

    def test_init_db_rebuilds_mixed_legacy_messages_table(self) -> None:
        conn = get_db_connection()
        try:
            session_id = _insert_session(conn, self.user_id, "Legacy mixed schema")
            cursor = conn.cursor()
            cursor.execute("DROP TABLE messages")
            cursor.execute(
                """
                CREATE TABLE messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    role TEXT NOT NULL,
                    content TEXT,
                    time TEXT NOT NULL,
                    is_result INTEGER NOT NULL DEFAULT 0,
                    title TEXT,
                    confidence TEXT,
                    description TEXT,
                    items_json TEXT,
                    total TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    user_id INTEGER,
                    message_type TEXT,
                    result_title TEXT,
                    result_confidence TEXT,
                    result_description TEXT,
                    result_items_json TEXT,
                    result_total TEXT
                );
                """
            )
            cursor.execute(
                """
                INSERT INTO messages (
                    session_id,
                    role,
                    content,
                    time,
                    is_result,
                    title,
                    confidence,
                    description,
                    items_json,
                    total,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    session_id,
                    "assistant",
                    "Balanced lunch with vegetables.",
                    "2026-03-13 12:30:00",
                    1,
                    "Lunch estimate",
                    "high",
                    "Estimated meal summary.",
                    '[{"name":"Rice","portion":"1 bowl","energy":"230 kcal"}]',
                    "230 kcal",
                    "2026-03-13 12:30:00",
                ),
            )
            conn.commit()
        finally:
            conn.close()

        init_db()

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(messages)")
            message_columns = {row["name"] for row in cursor.fetchall()}
            cursor.execute(
                """
                SELECT user_id, message_type, result_title, result_items_json, created_at
                FROM messages
                WHERE session_id = ?
                """,
                (session_id,),
            )
            message_row = cursor.fetchone()
        finally:
            conn.close()

        self.assertEqual(
            message_columns,
            {
                "id",
                "session_id",
                "user_id",
                "role",
                "message_type",
                "content",
                "payload_json",
                "result_title",
                "result_confidence",
                "result_description",
                "result_items_json",
                "result_total",
                "created_at",
            },
        )
        self.assertEqual(message_row["user_id"], self.user_id)
        self.assertEqual(message_row["message_type"], "estimate_result")
        self.assertEqual(message_row["result_title"], "Lunch estimate")
        self.assertEqual(
            message_row["result_items_json"],
            '[{"name":"Rice","portion":"1 bowl","energy":"230 kcal"}]',
        )
        self.assertEqual(message_row["created_at"], "2026-03-13 12:30:00")

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
