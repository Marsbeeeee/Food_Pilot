import os
import sqlite3
import tempfile
import unittest
from unittest.mock import patch

from backend.database.connection import get_db_connection
from backend.database.init_db import init_db
from backend.repositories.user_repository import (
    create_user,
    get_user_auth_by_email,
    get_user_by_id,
)
from backend.schemas.user import UserCreate


class UserRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_foodpilot.db")
        self.db_patch = patch("backend.database.connection.db_path", self.db_path)
        self.db_patch.start()
        init_db()

    def tearDown(self) -> None:
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def test_init_db_creates_users_table_with_expected_columns(self) -> None:
        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(users)")
            columns = {row["name"] for row in cursor.fetchall()}
        finally:
            conn.close()

        self.assertEqual(
            columns,
            {
                "id",
                "email",
                "password_hash",
                "display_name",
                "created_at",
                "updated_at",
            },
        )

    def test_create_and_fetch_user_round_trip(self) -> None:
        conn = get_db_connection()
        try:
            created = create_user(
                conn,
                UserCreate.model_validate(
                    {
                        "email": "alice@example.com",
                        "passwordHash": "hashed-password",
                        "displayName": "Alice",
                    }
                ),
            )
            fetched = get_user_by_id(conn, created.id)
            auth_row = get_user_auth_by_email(conn, "alice@example.com")
        finally:
            conn.close()

        self.assertIsNotNone(fetched)
        self.assertEqual(created.email, "alice@example.com")
        self.assertEqual(created.display_name, "Alice")
        self.assertIsNotNone(created.created_at)
        self.assertIsNotNone(created.updated_at)
        self.assertEqual(fetched.id, created.id)
        self.assertEqual(auth_row["password_hash"], "hashed-password")

    def test_duplicate_email_is_rejected(self) -> None:
        conn = get_db_connection()
        try:
            user = UserCreate.model_validate(
                {
                    "email": "alice@example.com",
                    "passwordHash": "hashed-password",
                    "displayName": "Alice",
                }
            )
            create_user(conn, user)
            with self.assertRaises(sqlite3.IntegrityError):
                create_user(conn, user)
        finally:
            conn.close()


if __name__ == "__main__":
    unittest.main()
