import unittest
from unittest.mock import patch

from backend.config.estimate import EstimateAIConfig
from backend.services.estimate import estimate_meal


class EstimateSingleDishBreakdownIntegrationTests(unittest.TestCase):
    def test_estimate_expands_single_dish_into_ingredient_items(self) -> None:
        config = EstimateAIConfig(
            api_key="test-key",
            model="qwen-plus",
            timeout_seconds=20,
            system_prompt="Base prompt",
            openai_base_url="https://example.com/v1",
        )
        ai_payload = {
            "title": "宫保鸡丁",
            "description": "经典川菜估算。",
            "confidence": "高",
            "items": [
                {
                    "name": "宫保鸡丁（主菜）",
                    "portion": "260 g",
                    "energy": "455 kcal",
                    "protein": "31.2 g",
                    "carbs": "20.8 g",
                    "fat": "26.0 g",
                }
            ],
            "total_calories": "455 kcal",
            "suggestion": "可减少油量和花生份量。",
        }

        with (
            patch("backend.services.estimate.get_estimate_ai_config", return_value=config),
            patch("backend.services.estimate.call_ai", return_value=ai_payload),
        ):
            result = estimate_meal("宫保鸡丁大概多少热量和三大营养素")

        self.assertEqual(result.itemization_mode, "single_dish_ingredients")
        self.assertGreaterEqual(len(result.items), 3)
        names = [item.name for item in result.items]
        self.assertIn("鸡胸肉", names)
        self.assertIn("黄瓜", names)
        self.assertIn("花生米", names)
        self.assertEqual(result.total_calories, "455 kcal")


if __name__ == "__main__":
    unittest.main()
