import unittest

from pydantic import ValidationError

from backend.schemas.estimate import EstimateRequest


class EstimateRequestSchemaTests(unittest.TestCase):
    def test_request_accepts_optional_client_request_id_profile_id_and_session_id(self) -> None:
        request_model = EstimateRequest.model_validate(
            {
                "query": "chicken salad",
                "clientRequestId": "estimate-123",
                "profileId": 12,
                "sessionId": 34,
            }
        )

        self.assertEqual(request_model.query, "chicken salad")
        self.assertEqual(request_model.client_request_id, "estimate-123")
        self.assertEqual(request_model.profile_id, 12)
        self.assertEqual(request_model.session_id, 34)

    def test_request_allows_missing_profile_id_and_session_id(self) -> None:
        request_model = EstimateRequest.model_validate({"query": "chicken salad"})

        self.assertEqual(request_model.query, "chicken salad")
        self.assertIsNone(request_model.client_request_id)
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

    def test_request_rejects_blank_client_request_id_when_provided(self) -> None:
        with self.assertRaises(ValidationError):
            EstimateRequest.model_validate(
                {
                    "query": "chicken salad",
                    "clientRequestId": "   ",
                }
            )


if __name__ == "__main__":
    unittest.main()
