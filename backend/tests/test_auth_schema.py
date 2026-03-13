import unittest

from backend.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from backend.schemas.user import UserOut


class AuthSchemaTests(unittest.TestCase):
    def test_register_request_accepts_camel_case_display_name(self) -> None:
        request = RegisterRequest.model_validate(
            {
                "email": " Alice@Example.com ",
                "password": "password123",
                "displayName": " Alice ",
            }
        )

        self.assertEqual(request.email, "alice@example.com")
        self.assertEqual(request.display_name, "Alice")

    def test_auth_response_serializes_aliases(self) -> None:
        response = AuthResponse(
            access_token="token-value",
            token_type="bearer",
            user=UserOut.model_validate(
                {
                    "id": 1,
                    "email": "alice@example.com",
                    "display_name": "Alice",
                    "created_at": "2026-03-13 18:00:00",
                    "updated_at": "2026-03-13 18:00:00",
                }
            ),
        )

        payload = response.model_dump(by_alias=True)

        self.assertIn("accessToken", payload)
        self.assertIn("tokenType", payload)
        self.assertIn("displayName", payload["user"])

    def test_login_request_requires_password(self) -> None:
        with self.assertRaises(ValueError):
            LoginRequest.model_validate(
                {
                    "email": "alice@example.com",
                    "password": "   ",
                }
            )


if __name__ == "__main__":
    unittest.main()
