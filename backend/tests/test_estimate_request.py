import unittest

from pydantic import ValidationError

from backend.schemas.estimate import EstimateRequest


class EstimateRequestSchemaTests(unittest.TestCase):
    def test_request_accepts_optional_profile_id_and_session_id(self) -> None:
        request_model = EstimateRequest.model_validate(
            {
                "query": "chicken salad",
                "profileId": 12,
                "sessionId": 34,
            }
        )

        self.assertEqual(request_model.query, "chicken salad")
        self.assertEqual(request_model.profile_id, 12)
        self.assertEqual(request_model.session_id, 34)

    def test_request_allows_missing_profile_id_and_session_id(self) -> None:
        request_model = EstimateRequest.model_validate({"query": "chicken salad"})

        self.assertEqual(request_model.query, "chicken salad")
        self.assertIsNone(request_model.profile_id)
        self.assertIsNone(request_model.session_id)

    def test_request_rejects_non_positive_session_id(self) -> None:
        with self.assertRaises(ValidationError):
            EstimateRequest.model_validate(
                {
                    "query": "chicken salad",
                    "sessionId": 0,
                }
            )


if __name__ == "__main__":
    unittest.main()
