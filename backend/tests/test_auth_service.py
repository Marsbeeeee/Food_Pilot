import os
import unittest
from unittest.mock import patch

from backend.database.init_db import init_db
from backend.schemas.auth import LoginRequest, RegisterRequest
from backend.schemas.profile import ProfileIn
from backend.services.auth_security import TokenValidationError
from backend.services.auth_service import (
    DuplicateEmailError,
    InvalidCredentialsError,
    delete_current_user,
    get_current_user,
    login_user,
    register_user,
)
from backend.services.profile_service import create_profile, get_profile_by_user_id
from backend.tests.test_db_utils import create_workspace_db_path, remove_file_if_exists


class AuthServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = create_workspace_db_path("auth-service-")
        remove_file_if_exists(self.db_path)
        self.db_patch = patch("backend.database.connection.db_path", self.db_path)
        self.db_patch.start()
        init_db()

    def tearDown(self) -> None:
        self.db_patch.stop()
        remove_file_if_exists(self.db_path)

    def test_register_login_and_get_current_user_round_trip(self) -> None:
        register_response = register_user(
            RegisterRequest.model_validate(
                {
                    "email": "alice@example.com",
                    "password": "password123",
                    "displayName": "Alice",
                }
            )
        )

        login_response = login_user(
            LoginRequest.model_validate(
                {
                    "email": "alice@example.com",
                    "password": "password123",
                }
            )
        )
        current_user = get_current_user(login_response.access_token)

        self.assertEqual(register_response.user.email, "alice@example.com")
        self.assertEqual(register_response.user.display_name, "Alice")
        self.assertEqual(login_response.user.id, register_response.user.id)
        self.assertEqual(current_user.id, register_response.user.id)

    def test_register_rejects_duplicate_email(self) -> None:
        request = RegisterRequest.model_validate(
            {
                "email": "alice@example.com",
                "password": "password123",
                "displayName": "Alice",
            }
        )

        register_user(request)

        with self.assertRaises(DuplicateEmailError):
            register_user(request)

    def test_login_rejects_invalid_password(self) -> None:
        register_user(
            RegisterRequest.model_validate(
                {
                    "email": "alice@example.com",
                    "password": "password123",
                    "displayName": "Alice",
                }
            )
        )

        with self.assertRaises(InvalidCredentialsError):
            login_user(
                LoginRequest.model_validate(
                    {
                        "email": "alice@example.com",
                        "password": "wrong-password",
                    }
                )
            )

    def test_get_current_user_rejects_invalid_token(self) -> None:
        with self.assertRaises(TokenValidationError):
            get_current_user("invalid-token")

    def test_delete_current_user_removes_user_and_profile(self) -> None:
        register_response = register_user(
            RegisterRequest.model_validate(
                {
                    "email": "alice@example.com",
                    "password": "password123",
                    "displayName": "Alice",
                }
            )
        )
        create_profile(
            register_response.user.id,
            ProfileIn.model_validate(
                {
                    "age": 28,
                    "height": 170,
                    "weight": 65,
                    "sex": "Female",
                    "activityLevel": "Lightly active",
                    "exerciseType": "Running",
                    "goal": "Fat loss",
                    "pace": "Moderate",
                    "kcalTarget": 1800,
                    "dietStyle": "Balanced",
                    "allergies": ["Peanut"],
                }
            ),
        )

        delete_current_user(register_response.user.id)

        self.assertIsNone(get_profile_by_user_id(register_response.user.id))
        with self.assertRaises(InvalidCredentialsError):
            get_current_user(register_response.access_token)


if __name__ == "__main__":
    unittest.main()
