import unittest

from backend.schemas.estimate import EstimateRequest


class EstimateRequestSchemaTests(unittest.TestCase):
    def test_request_accepts_optional_profile_id(self) -> None:
        request_model = EstimateRequest.model_validate(
            {
                "query": "鸡胸肉沙拉",
                "profileId": 12,
            }
        )

        self.assertEqual(request_model.query, "鸡胸肉沙拉")
        self.assertEqual(request_model.profile_id, 12)

    def test_request_allows_missing_profile_id(self) -> None:
        request_model = EstimateRequest.model_validate({"query": "鸡胸肉沙拉"})

        self.assertEqual(request_model.query, "鸡胸肉沙拉")
        self.assertIsNone(request_model.profile_id)


if __name__ == "__main__":
    unittest.main()
