import unittest
from unittest.mock import ANY, Mock, patch

from backend.schemas.estimate import EstimateRequest, EstimateResult
from backend.services.estimate_service import create_estimate_response


class EstimateServiceProfileTests(unittest.TestCase):
    def test_create_estimate_response_forwards_profile_id_user_id_and_session_id(self) -> None:
        request_model = EstimateRequest(query="chicken salad", profileId=12, sessionId=56)
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
        ) as estimate_meal_mock, patch(
            "backend.services.estimate_service.get_db_connection",
            return_value=Mock(),
        ) as get_db_connection_mock, patch(
            "backend.services.estimate_service._resolve_food_log_session_id",
            return_value=56,
        ) as resolve_session_id_mock, patch(
            "backend.services.estimate_service.create_food_log_from_estimate",
        ) as record_food_log_mock:
            status_code, response = create_estimate_response(request_model, 34)

        self.assertEqual(status_code, 200)
        self.assertTrue(response.success)
        estimate_meal_mock.assert_called_once_with("chicken salad", 12, 34)
        get_db_connection_mock.assert_called_once()
        resolve_session_id_mock.assert_called_once()
        record_food_log_mock.assert_called_once_with(
            34,
            "chicken salad",
            estimate_result,
            source_type="estimate_api",
            session_id=56,
            conn=ANY,
        )


if __name__ == "__main__":
    unittest.main()
