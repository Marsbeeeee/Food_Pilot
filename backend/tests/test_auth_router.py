import unittest
from unittest.mock import patch

from fastapi import HTTPException

from backend.dependencies.auth import get_current_user
from backend.routers.auth import login, register
from backend.schemas.auth import LoginRequest, RegisterRequest
from backend.schemas.user import UserOut
from backend.services.auth_service import DuplicateEmailError, InvalidCredentialsError


class AuthRouterTests(unittest.TestCase):
    def test_register_maps_duplicate_email_to_409(self) -> None:
        request = RegisterRequest.model_validate(
            {
                "email": "alice@example.com",
                "password": "password123",
                "displayName": "Alice",
            }
        )

        with patch(
            "backend.routers.auth.register_user",
            side_effect=DuplicateEmailError("email already exists"),
        ):
            with self.assertRaises(HTTPException) as exc:
                register(request)

        self.assertEqual(exc.exception.status_code, 409)

    def test_login_maps_invalid_credentials_to_401(self) -> None:
        request = LoginRequest.model_validate(
            {
                "email": "alice@example.com",
                "password": "password123",
            }
        )

        with patch(
            "backend.routers.auth.login_user",
            side_effect=InvalidCredentialsError("invalid"),
        ):
            with self.assertRaises(HTTPException) as exc:
                login(request)

        self.assertEqual(exc.exception.status_code, 401)

    def test_get_current_user_dependency_requires_bearer_token(self) -> None:
        with self.assertRaises(HTTPException) as exc:
            get_current_user("Basic abc")

        self.assertEqual(exc.exception.status_code, 401)

    def test_get_current_user_dependency_returns_user(self) -> None:
        user = UserOut.model_validate(
            {
                "id": 1,
                "email": "alice@example.com",
                "display_name": "Alice",
                "created_at": "2026-03-13 18:00:00",
                "updated_at": "2026-03-13 18:00:00",
            }
        )

        with patch("backend.dependencies.auth.get_current_user_record", return_value=user):
            current_user = get_current_user("Bearer token-123")

        self.assertEqual(current_user.id, 1)


if __name__ == "__main__":
    unittest.main()
