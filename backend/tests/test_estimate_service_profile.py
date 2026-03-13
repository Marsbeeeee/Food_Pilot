import unittest
from unittest.mock import patch

from backend.schemas.estimate import EstimateRequest, EstimateResult
from backend.services.estimate_service import create_estimate_response


class EstimateServiceProfileTests(unittest.TestCase):
    def test_create_estimate_response_forwards_profile_id_and_user_id(self) -> None:
        request_model = EstimateRequest(query="chicken salad", profileId=12)
        estimate_result = EstimateResult(
            title="Chicken salad",
            description="Lean protein and vegetables.",
            confidence="High",
            items=[
                {
                    "name": "Chicken breast",
                    "portion": "150g",
                    "energy": "240 kcal",
                }
            ],
            total_calories="240 kcal",
            suggestion="Works well as a lighter meal.",
        )

        with patch(
            "backend.services.estimate_service.estimate_meal",
            return_value=estimate_result,
        ) as estimate_meal_mock:
            status_code, response = create_estimate_response(request_model, 34)

        self.assertEqual(status_code, 200)
        self.assertTrue(response.success)
        estimate_meal_mock.assert_called_once_with("chicken salad", 12, 34)


if __name__ == "__main__":
    unittest.main()
