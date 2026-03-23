import unittest
from unittest.mock import patch

from backend.config.estimate import EstimateAIConfig
from backend.services.estimate import estimate_meal


class EstimateMultiFoodRetryTests(unittest.TestCase):
    def test_estimate_retries_with_split_instruction_when_multi_food_hits_but_single_item(self) -> None:
        config = EstimateAIConfig(
            api_key="test-key",
            model="qwen-plus",
            timeout_seconds=20,
            system_prompt="Base prompt",
            openai_base_url="https://example.com/v1",
        )
        first_payload = {
            "title": "早餐估算",
            "description": "初次返回未拆分。",
            "confidence": "中",
            "items": [
                {
                    "name": "包子豆浆套餐",
                    "portion": "一份",
                    "energy": "480 kcal",
                    "protein": "15 g",
                    "carbs": "66 g",
                    "fat": "17 g",
                }
            ],
            "total_calories": "480 kcal",
            "suggestion": "注意控制主食总量。",
        }
        second_payload = {
            "title": "早餐估算",
            "description": "重试后拆分。",
            "confidence": "中",
            "items": [
                {
                    "name": "猪肉白菜包子",
                    "portion": "2个",
                    "energy": "400 kcal",
                    "protein": "14 g",
                    "carbs": "52 g",
                    "fat": "14 g",
                },
                {
                    "name": "无糖豆浆",
                    "portion": "1杯",
                    "energy": "80 kcal",
                    "protein": "7 g",
                    "carbs": "4 g",
                    "fat": "3 g",
                },
            ],
            "total_calories": "480 kcal",
            "suggestion": "这顿以碳水为主，可搭配额外蛋白质。",
        }

        with (
            patch("backend.services.estimate.get_estimate_ai_config", return_value=config),
            patch("backend.services.estimate.call_ai", side_effect=[first_payload, second_payload]) as call_ai_mock,
        ):
            result = estimate_meal("早餐两个包子一杯豆浆大概多少热量")

        self.assertEqual(len(result.items), 2)
        self.assertEqual(result.items[0].name, "猪肉白菜包子")
        self.assertEqual(result.items[1].name, "无糖豆浆")
        self.assertEqual(call_ai_mock.call_count, 2)

        second_prompt = call_ai_mock.call_args_list[1].args[1]
        self.assertIn("Return at least", second_prompt)
        self.assertIn("Do not merge multiple foods", second_prompt)


if __name__ == "__main__":
    unittest.main()
