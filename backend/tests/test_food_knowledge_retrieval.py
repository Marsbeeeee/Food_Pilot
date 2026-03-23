import unittest
from pathlib import Path
from unittest.mock import patch

from backend.config.food_knowledge import FoodKnowledgeConfig
from backend.services.food_knowledge import (
    build_single_dish_ingredient_breakdown,
    retrieve_food_knowledge,
)


class FoodKnowledgeRetrievalTests(unittest.TestCase):
    def setUp(self) -> None:
        self.data_path = Path(__file__).resolve().parents[1] / "data" / "chinese_food_kb_seed.json"

    def _patch_config(self):
        return patch(
            "backend.services.food_knowledge.get_food_knowledge_config",
            return_value=FoodKnowledgeConfig(
                enabled=True,
                data_path=self.data_path,
                top_k=3,
                min_score=1.0,
                max_context_chars=1200,
                only_chinese=True,
            ),
        )

    def test_retrieve_hits_beef_noodle_for_chinese_estimate_query(self) -> None:
        with self._patch_config():
            result = retrieve_food_knowledge("一碗牛肉面加鸡蛋大概多少热量", scenario="estimate")

        self.assertTrue(result.has_hits)
        self.assertGreaterEqual(result.hit_count, 1)
        self.assertIn("Chinese food knowledge context", result.context_text)
        self.assertTrue(any(ref["food_name"] == "牛肉面" for ref in result.references))
        self.assertTrue(all(ref.get("source_name") for ref in result.references))

    def test_retrieve_returns_non_chinese_reason_for_english_query(self) -> None:
        with self._patch_config():
            result = retrieve_food_knowledge("how many calories in chicken salad", scenario="estimate")

        self.assertFalse(result.has_hits)
        self.assertEqual(result.reason, "non_chinese_query")
        self.assertEqual(result.references, [])

    def test_retrieve_hits_milk_tea_for_recommendation_query(self) -> None:
        with self._patch_config():
            result = retrieve_food_knowledge("奶茶有没有更健康的替代", scenario="meal_recommendation")

        self.assertTrue(result.has_hits)
        self.assertTrue(any(ref["food_name"] == "珍珠奶茶" for ref in result.references))
        self.assertIn("References:", result.context_text)

    def test_build_single_dish_ingredient_breakdown_for_kungpao_chicken(self) -> None:
        with self._patch_config():
            items = build_single_dish_ingredient_breakdown(
                "宫保鸡丁大概多少热量",
                primary_item_name="宫保鸡丁（主菜）",
                total_calories_text="455 kcal",
                primary_portion_text="260 g",
            )

        self.assertIsNotNone(items)
        assert items is not None
        self.assertGreaterEqual(len(items), 3)
        names = [item["name"] for item in items]
        self.assertIn("鸡胸肉", names)
        self.assertIn("黄瓜", names)
        self.assertIn("花生米", names)
        self.assertTrue(all("energy" in item for item in items))
        self.assertTrue(all("portion" in item for item in items))


if __name__ == "__main__":
    unittest.main()
