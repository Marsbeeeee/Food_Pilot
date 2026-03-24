import unittest
from unittest.mock import patch

from backend.config.estimate import EstimateAIConfig
from backend.services.recommendation import generate_text_reply


class TextFoodKnowledgeIntegrationTests(unittest.TestCase):
    def test_text_reply_attaches_knowledge_refs_and_injects_context_into_prompt(self) -> None:
        config = EstimateAIConfig(
            api_key="test-key",
            model="qwen-plus",
            timeout_seconds=20,
            system_prompt="Base prompt",
            openai_base_url="https://example.com/v1",
        )
        ai_payload = {
            "title": "补充说明",
            "description": "解释为什么低糖奶茶仍需控制频率。",
            "response": "低糖能减少糖负担，但奶和配料仍然会带来额外热量。",
        }

        with (
            patch("backend.services.recommendation.get_estimate_ai_config", return_value=config),
            patch("backend.services.recommendation.call_ai", return_value=ai_payload) as call_ai_mock,
        ):
            result = generate_text_reply("为什么低糖珍珠奶茶也不能多喝")

        self.assertIsNotNone(result.knowledge_refs)
        self.assertTrue(any(ref.food_name == "低糖珍珠奶茶" for ref in result.knowledge_refs or []))

        call_args = call_ai_mock.call_args
        self.assertIsNotNone(call_args)
        system_prompt = call_args.args[1]
        self.assertIn("Chinese food knowledge context", system_prompt)
        self.assertIn("低糖珍珠奶茶", system_prompt)


if __name__ == "__main__":
    unittest.main()
