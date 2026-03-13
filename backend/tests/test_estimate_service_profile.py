import unittest
from unittest.mock import patch

from backend.schemas.estimate import EstimateRequest, EstimateResult
from backend.services.estimate_service import create_estimate_response


class EstimateServiceProfileTests(unittest.TestCase):
    def test_create_estimate_response_forwards_profile_id(self) -> None:
        request_model = EstimateRequest(query="鸡胸肉沙拉", profileId=12)
        estimate_result = EstimateResult(
            title="鸡胸肉沙拉",
            description="高蛋白、清淡。",
            confidence="高",
            items=[
                {
                    "name": "鸡胸肉",
                    "portion": "150g",
                    "energy": "240 kcal",
                }
            ],
            total_calories="240 kcal",
            suggestion="适合作为轻负担餐食。",
        )

        with patch(
            "backend.services.estimate_service.estimate_meal",
            return_value=estimate_result,
        ) as estimate_meal_mock:
            status_code, response = create_estimate_response(request_model)

        self.assertEqual(status_code, 200)
        self.assertTrue(response.success)
        estimate_meal_mock.assert_called_once_with("鸡胸肉沙拉", 12)


if __name__ == "__main__":
    unittest.main()
