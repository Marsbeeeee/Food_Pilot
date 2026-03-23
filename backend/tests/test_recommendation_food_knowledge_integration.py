import unittest
from unittest.mock import patch

from backend.config.estimate import EstimateAIConfig
from backend.services.recommendation import generate_meal_recommendation


class RecommendationFoodKnowledgeIntegrationTests(unittest.TestCase):
    def test_recommendation_attaches_knowledge_refs_and_injects_context_into_prompt(self) -> None:
        config = EstimateAIConfig(
            api_key="test-key",
            model="qwen-plus",
            timeout_seconds=20,
            system_prompt="Base prompt",
            openai_base_url="https://example.com/v1",
        )
        ai_payload = {
            "title": "奶茶替代建议",
            "description": "先降糖再替代高糖配料。",
            "response": "先改成三分糖去奶盖，再逐步替换为无糖豆浆或美式咖啡。",
        }

        with (
            patch("backend.services.recommendation.get_estimate_ai_config", return_value=config),
            patch("backend.services.recommendation.call_ai", return_value=ai_payload) as call_ai_mock,
        ):
            result = generate_meal_recommendation("奶茶有没有更健康的平替")

        self.assertIsNotNone(result.knowledge_refs)
        self.assertTrue(any(ref.food_name == "珍珠奶茶" for ref in result.knowledge_refs or []))

        call_args = call_ai_mock.call_args
        self.assertIsNotNone(call_args)
        system_prompt = call_args.args[1]
        self.assertIn("Chinese food knowledge context", system_prompt)
        self.assertIn("珍珠奶茶", system_prompt)


if __name__ == "__main__":
    unittest.main()
