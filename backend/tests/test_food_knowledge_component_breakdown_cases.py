import unittest
from pathlib import Path
from unittest.mock import patch

from backend.config.food_knowledge import FoodKnowledgeConfig
from backend.services.food_knowledge import build_single_dish_ingredient_breakdown


class FoodKnowledgeComponentBreakdownCaseTests(unittest.TestCase):
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

    def test_build_single_dish_ingredient_breakdown_for_lajiaochaorou_alias_contains_macros(self) -> None:
        with self._patch_config():
            items = build_single_dish_ingredient_breakdown(
                "辣椒炒肉热量多少",
                primary_item_name="辣椒炒肉",
                total_calories_text="290 kcal",
                primary_portion_text="约200 g",
                primary_protein_text="18.5 g",
                primary_carbs_text="6.2 g",
                primary_fat_text="19.2 g",
            )

        self.assertIsNotNone(items)
        assert items is not None
        self.assertEqual(len(items), 3)
        names = [item["name"] for item in items]
        self.assertIn("猪瘦肉末", names)
        self.assertIn("青椒", names)
        self.assertIn("植物油（炒制用）", names)
        self.assertTrue(all("protein" in item or "carbs" in item or "fat" in item for item in items))


if __name__ == "__main__":
    unittest.main()
