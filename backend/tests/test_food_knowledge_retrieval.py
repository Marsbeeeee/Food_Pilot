import json
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
        self.assertTrue(all(ref.get("food_id") for ref in result.references))
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
        self.assertTrue(all(ref.get("source_id") for ref in result.references))
        self.assertTrue(all(ref.get("source_name") for ref in result.references))

    def test_dataset_has_required_fields_traceability_and_minimum_size(self) -> None:
        payload = json.loads(self.data_path.read_text(encoding="utf-8"))
        foods = payload["foods"]
        self.assertGreaterEqual(len(foods), 60)
        self.assertEqual(len({food["canonical_name"] for food in foods}), len(foods))
        self.assertEqual(payload["version"], "2026-03-24")
        self.assertTrue(any(item["version"] == payload["version"] for item in payload["change_summary"]))

        source_ids = {source["id"] for source in payload["sources"]}
        for food in foods:
            self.assertTrue((food.get("food_id") or food.get("id") or "").strip())
            self.assertTrue(food["canonical_name"].strip())
            self.assertTrue(food["aliases"])
            self.assertTrue(food["portion_hints"])
            self.assertTrue(food["source_ids"])
            self.assertTrue(food["updated_at"].strip())
            self.assertEqual(set(food["nutrition_per_100g"]), {"kcal", "protein_g", "carbs_g", "fat_g"})
            self.assertTrue(set(food["source_ids"]).issubset(source_ids))

    def test_retrieve_hits_low_sugar_milk_tea_variant_with_traceable_refs(self) -> None:
        with self._patch_config():
            result = retrieve_food_knowledge("三分糖珍珠奶茶是不是更轻一点", scenario="meal_recommendation")

        self.assertTrue(result.has_hits)
        self.assertTrue(any(ref["food_name"] == "低糖珍珠奶茶" for ref in result.references))
        self.assertTrue(
            all(
                ref.get("food_id") and ref.get("food_name") and ref.get("source_id") and ref.get("source_name")
                for ref in result.references
            )
        )

    def test_retrieve_hits_local_alias_for_lanzhou_beef_noodle(self) -> None:
        with self._patch_config():
            result = retrieve_food_knowledge("兰州拉面热量高吗", scenario="estimate")

        self.assertTrue(result.has_hits)
        self.assertTrue(any(ref["food_name"] == "兰州牛肉面" for ref in result.references))
        self.assertTrue(all(ref.get("source_name") for ref in result.references))

    def test_retrieve_prefers_low_sugar_variant_for_half_sugar_milk_tea(self) -> None:
        with self._patch_config():
            result = retrieve_food_knowledge("半糖珍珠奶茶热量高吗", scenario="estimate")

        self.assertTrue(result.has_hits)
        self.assertEqual(result.references[0]["food_name"], "低糖珍珠奶茶")
        self.assertIn("珍珠奶茶", [ref["food_name"] for ref in result.references])

    def test_retrieve_prefers_doufunao_alias_over_generic_tofu_in_breakfast_compare(self) -> None:
        with self._patch_config():
            result = retrieve_food_knowledge("豆腐花和云吞哪个更适合早餐", scenario="meal_recommendation")

        self.assertTrue(result.has_hits)
        foods = [ref["food_name"] for ref in result.references]
        self.assertEqual(foods[0], "豆腐脑")
        self.assertIn("馄饨", foods)

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

    def test_retrieve_hits_convenience_store_tuna_sandwich(self) -> None:
        with self._patch_config():
            result = retrieve_food_knowledge("便利店金枪鱼全麦三明治热量高吗", scenario="estimate")

        self.assertTrue(result.has_hits)
        self.assertEqual(result.references[0]["food_name"], "金枪鱼全麦三明治")
        self.assertEqual(result.references[0]["food_id"], "tuna-wholewheat-sandwich")

    def test_retrieve_hits_fitness_meal_for_brown_rice_chicken_bowl(self) -> None:
        with self._patch_config():
            result = retrieve_food_knowledge("糙米鸡胸健身餐适合减脂吗", scenario="meal_recommendation")

        self.assertTrue(result.has_hits)
        self.assertEqual(result.references[0]["food_name"], "糙米鸡胸健身餐")
        self.assertEqual(result.references[0]["food_id"], "brown-rice-chicken-fitness-bowl")


if __name__ == "__main__":
    unittest.main()
