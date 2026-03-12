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
        request_model = EstimateRequest(query="鸡胸肉沙拉")
        estimate_result = EstimateResult(
            title="鸡胸肉沙拉",
            description="高蛋白、低油脂。",
            confidence="高",
            items=[
                {
                    "name": "鸡胸肉",
                    "portion": "150g",
                    "energy": "240 kcal",
                }
            ],
            total_calories="240 kcal",
            suggestion="可以补充一些碳水。",
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
        self.assertEqual(response.data.title, "鸡胸肉沙拉")
        self.assertEqual(response.data.total_calories, "240 kcal")
        self.assertEqual(response.data.items[0].name, "鸡胸肉")

    def test_validation_error_response_has_unified_structure(self) -> None:
        with self.assertRaises(Exception) as context:
            EstimateRequest.model_validate({"query": " "})

        validation_error = context.exception
        response = create_estimate_validation_error_response(validation_error.errors())
        payload = json.loads(response.body)

        self.assertEqual(response.status_code, 422)
        self.assertFalse(payload["success"])
        self.assertIsNone(payload["data"])
        self.assertEqual(payload["error"]["code"], "VALIDATION_ERROR")
        self.assertFalse(payload["error"]["retryable"])
        self.assertEqual(payload["error"]["fields"][0]["field"], "query")

    def test_ai_error_returns_fallback_structure(self) -> None:
        request_model = EstimateRequest(query="蛋炒饭")

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
        self.assertEqual(response.error.code, "AI_UPSTREAM_ERROR")
        self.assertEqual(response.error.message, "AI 服务暂时不可用，请稍后重试。")
        self.assertTrue(response.error.retryable)


if __name__ == "__main__":
    unittest.main()
