import unittest

from backend.services.auth_security import (
    TokenValidationError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


class AuthSecurityTests(unittest.TestCase):
    def test_hash_password_round_trip(self) -> None:
        password_hash = hash_password("password123")

        self.assertNotEqual(password_hash, "password123")
        self.assertTrue(verify_password("password123", password_hash))
        self.assertFalse(verify_password("wrong-password", password_hash))

    def test_decode_access_token_returns_subject(self) -> None:
        token = create_access_token(12)

        payload = decode_access_token(token)

        self.assertEqual(payload["sub"], "12")

    def test_decode_access_token_rejects_invalid_signature(self) -> None:
        token = create_access_token(12)
        invalid_token = f"{token}tampered"

        with self.assertRaises(TokenValidationError):
            decode_access_token(invalid_token)


if __name__ == "__main__":
    unittest.main()
