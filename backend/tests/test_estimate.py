import json
import unittest
from unittest.mock import patch

from backend.schemas.estimate import EstimateRequest, EstimateResult
from backend.services import estimate as estimate_module
from backend.services.estimate_service import (
    create_estimate_response,
    create_estimate_validation_error_response,
)


class EstimateTests(unittest.TestCase):
    def test_success_response_has_expected_structure(self) -> None:
        request_model = EstimateRequest(
            query="chicken salad",
            clientRequestId="estimate-123",
        )
        estimate_result = EstimateResult(
            title="Chicken Salad",
            description="Lean protein with vegetables.",
            confidence="High",
            items=[
                {
                    "name": "Chicken breast",
                    "portion": "150g",
                    "energy": "240 kcal",
                }
            ],
            total_calories="240 kcal",
            suggestion="Add more greens for extra fiber.",
        )

        with patch(
            "backend.services.estimate_service.estimate_meal",
            return_value=estimate_result,
        ):
            status_code, response = create_estimate_response(request_model)

        self.assertEqual(status_code, 200)
        self.assertTrue(response.success)
        self.assertIsNone(response.error)
        self.assertIsNotNone(response.data)
        self.assertEqual(response.client_request_id, "estimate-123")
        self.assertIsNone(response.food_log_id)
        self.assertEqual(response.save_status, "not_saved")
        self.assertEqual(response.data.title, "Chicken Salad")
        self.assertEqual(response.data.total_calories, "240 kcal")
        self.assertEqual(response.data.items[0].name, "Chicken breast")

    def test_validation_error_response_has_unified_structure(self) -> None:
        with self.assertRaises(Exception) as context:
            EstimateRequest.model_validate({"query": " "})

        validation_error = context.exception
        response = create_estimate_validation_error_response(validation_error.errors())
        payload = json.loads(response.body)

        self.assertEqual(response.status_code, 422)
        self.assertFalse(payload["success"])
        self.assertIsNone(payload["data"])
        self.assertIsNone(payload["clientRequestId"])
        self.assertIsNone(payload["foodLogId"])
        self.assertEqual(payload["saveStatus"], "not_saved")
        self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")
        self.assertEqual(payload["error"]["message"], "请求参数校验失败。")
        self.assertFalse(payload["error"]["retryable"])
        self.assertEqual(payload["error"]["fields"][0]["field"], "query")
        self.assertEqual(payload["error"]["fields"][0]["message"], "输入内容不能为空")

    def test_ai_error_returns_fallback_structure(self) -> None:
        request_model = EstimateRequest(
            query="fried rice",
            clientRequestId="estimate-456",
        )

        with patch(
            "backend.services.estimate_service.estimate_meal",
            side_effect=estimate_module.UpstreamAIError(
                "AI provider request failed (503).",
                retryable=True,
            ),
        ):
            status_code, response = create_estimate_response(request_model)

        self.assertEqual(status_code, 503)
        self.assertFalse(response.success)
        self.assertIsNone(response.data)
        self.assertIsNotNone(response.error)
        self.assertEqual(response.client_request_id, "estimate-456")
        self.assertIsNone(response.food_log_id)
        self.assertEqual(response.save_status, "not_saved")
        self.assertEqual(response.error.code, "AI_UPSTREAM_ERROR")
        self.assertEqual(response.error.message, "AI 服务暂时不可用，请稍后重试。")
        self.assertTrue(response.error.retryable)


if __name__ == "__main__":
    unittest.main()
