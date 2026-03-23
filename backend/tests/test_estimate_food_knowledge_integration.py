import unittest
from unittest.mock import patch

from backend.config.estimate import EstimateAIConfig
from backend.services.estimate import estimate_meal


class EstimateFoodKnowledgeIntegrationTests(unittest.TestCase):
    def test_estimate_attaches_knowledge_refs_and_injects_context_into_prompt(self) -> None:
        config = EstimateAIConfig(
            api_key="test-key",
            model="qwen-plus",
            timeout_seconds=20,
            system_prompt="Base prompt",
            openai_base_url="https://example.com/v1",
        )
        ai_payload = {
            "title": "牛肉面估算",
            "description": "按常见一大碗估算。",
            "confidence": "中",
            "items": [
                {
                    "name": "牛肉面",
                    "portion": "一大碗",
                    "energy": "720 kcal",
                    "protein": "28 g",
                    "carbs": "86 g",
                    "fat": "28 g",
                }
            ],
            "total_calories": "720 kcal",
            "suggestion": "可减少面量并少喝汤底。",
        }

        with (
            patch("backend.services.estimate.get_estimate_ai_config", return_value=config),
            patch("backend.services.estimate.call_ai", return_value=ai_payload) as call_ai_mock,
        ):
            result = estimate_meal("一碗牛肉面大概多少热量")

        self.assertIsNotNone(result.knowledge_refs)
        self.assertTrue(any(ref.food_name == "牛肉面" for ref in result.knowledge_refs or []))

        call_args = call_ai_mock.call_args
        self.assertIsNotNone(call_args)
        system_prompt = call_args.args[1]
        self.assertIn("Chinese food knowledge context", system_prompt)
        self.assertIn("牛肉面", system_prompt)


if __name__ == "__main__":
    unittest.main()
