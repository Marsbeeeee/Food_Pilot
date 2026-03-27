import unittest
from types import SimpleNamespace
from unittest.mock import patch

from backend.config.estimate import EstimateAIConfig
from backend.services.estimate import estimate_meal
from backend.services.estimate_parser import split_estimate_by_items


class EstimateCardItemizationRuleTests(unittest.TestCase):
    def setUp(self) -> None:
        self.config = EstimateAIConfig(
            api_key="test-key",
            model="qwen-plus",
            timeout_seconds=20,
            system_prompt="Base prompt",
            openai_base_url="https://example.com/v1",
        )

    def test_single_dish_query_does_not_retry_only_because_knowledge_hits_multiple_entries(self) -> None:
        ai_payload = {
            "title": "肉末茄子",
            "description": "家常炒菜估算。",
            "confidence": "中",
            "items": [
                {
                    "name": "肉末茄子",
                    "portion": "1份",
                    "energy": "330 kcal",
                    "protein": "14 g",
                    "carbs": "18 g",
                    "fat": "22 g",
                }
            ],
            "total_calories": "330 kcal",
            "suggestion": "如果少油一些，热量会更低。",
        }

        with (
            patch("backend.services.estimate.get_estimate_ai_config", return_value=self.config),
            patch(
                "backend.services.estimate.retrieve_food_knowledge",
                return_value=SimpleNamespace(
                    context_text="ctx",
                    has_hits=True,
                    hit_count=3,
                    references=[],
                ),
            ),
            patch("backend.services.estimate.build_single_dish_ingredient_breakdown", return_value=None),
            patch("backend.services.estimate.call_ai", return_value=ai_payload) as call_ai_mock,
        ):
            result = estimate_meal("肉末茄子大概多少热量")

        self.assertEqual(call_ai_mock.call_count, 1)
        self.assertEqual(len(result.items), 1)
        self.assertIsNone(result.itemization_mode)

    def test_single_dish_component_items_stay_in_one_card(self) -> None:
        ai_payload = {
            "title": "肉末茄子",
            "description": "按组成项拆解的估算。",
            "confidence": "中",
            "items": [
                {
                    "name": "长茄",
                    "portion": "200 g",
                    "energy": "36 kcal",
                    "protein": "1.4 g",
                    "carbs": "7.2 g",
                    "fat": "0.3 g",
                },
                {
                    "name": "猪瘦肉末",
                    "portion": "80 g",
                    "energy": "144 kcal",
                    "protein": "16.0 g",
                    "carbs": "0 g",
                    "fat": "8.0 g",
                },
                {
                    "name": "植物油",
                    "portion": "15 g",
                    "energy": "135 kcal",
                    "protein": "0 g",
                    "carbs": "0 g",
                    "fat": "15.0 g",
                },
            ],
            "total_calories": "315 kcal",
            "suggestion": "控制用油会更稳妥。",
        }

        with (
            patch("backend.services.estimate.get_estimate_ai_config", return_value=self.config),
            patch(
                "backend.services.estimate.retrieve_food_knowledge",
                return_value=SimpleNamespace(
                    context_text="ctx",
                    has_hits=True,
                    hit_count=3,
                    references=[],
                ),
            ),
            patch(
                "backend.services.estimate.build_single_dish_ingredient_breakdown",
                return_value=[
                    {"name": "长茄", "portion": "适量", "energy": "36 kcal"},
                    {"name": "猪瘦肉末", "portion": "适量", "energy": "144 kcal"},
                ],
            ),
            patch("backend.services.estimate.call_ai", return_value=ai_payload) as call_ai_mock,
        ):
            result = estimate_meal("肉末茄子大概多少热量")

        self.assertEqual(call_ai_mock.call_count, 1)
        self.assertEqual(result.itemization_mode, "single_dish_ingredients")
        self.assertEqual(len(split_estimate_by_items(result)), 1)
        self.assertEqual(len(result.items), 3)

    def test_single_dish_multi_component_rows_stay_in_one_card_without_kb_breakdown(self) -> None:
        ai_payload = {
            "title": "番茄炒蛋盖饭",
            "description": "常见中式家常盖饭。",
            "confidence": "高",
            "items": [
                {
                    "name": "白米饭（熟）",
                    "portion": "150 克（约1碗）",
                    "energy": "195 kcal",
                    "protein": "3.8 g",
                    "carbs": "43.2 g",
                    "fat": "0.4 g",
                },
                {
                    "name": "鸡蛋（全蛋）",
                    "portion": "2个（约100克）",
                    "energy": "155 kcal",
                    "protein": "12.6 g",
                    "carbs": "1.1 g",
                    "fat": "10.6 g",
                },
                {
                    "name": "番茄（生）",
                    "portion": "150 克（约1个中等大小）",
                    "energy": "33 kcal",
                    "protein": "1.2 g",
                    "carbs": "7.2 g",
                    "fat": "0.3 g",
                },
                {
                    "name": "烹饪用油",
                    "portion": "10 克（约1小勺）",
                    "energy": "90 kcal",
                    "protein": "0 g",
                    "carbs": "0 g",
                    "fat": "10.0 g",
                },
            ],
            "total_calories": "473 kcal",
            "suggestion": "如果想再轻一些，可以减少油和米饭份量。",
        }

        with (
            patch("backend.services.estimate.get_estimate_ai_config", return_value=self.config),
            patch(
                "backend.services.estimate.retrieve_food_knowledge",
                return_value=SimpleNamespace(
                    context_text="ctx",
                    has_hits=True,
                    hit_count=1,
                    references=[],
                ),
            ),
            patch("backend.services.estimate.build_single_dish_ingredient_breakdown", return_value=None),
            patch("backend.services.estimate.call_ai", return_value=ai_payload),
        ):
            result = estimate_meal("一万卤肉饭的热量")

        self.assertEqual(result.itemization_mode, "single_dish_ingredients")
        self.assertEqual(len(result.items), 4)
        self.assertEqual(len(split_estimate_by_items(result)), 1)


if __name__ == "__main__":
    unittest.main()
