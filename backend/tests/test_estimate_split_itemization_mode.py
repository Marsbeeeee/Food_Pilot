import unittest

from backend.schemas.estimate import EstimateItem, EstimateResult
from backend.services.estimate_parser import split_estimate_by_items


class EstimateSplitItemizationModeTests(unittest.TestCase):
    def test_split_estimate_by_items_keeps_single_card_for_single_dish_ingredient_breakdown(self) -> None:
        estimate = EstimateResult(
            title="宫保鸡丁",
            description="单菜品按食材拆分",
            confidence="高",
            items=[
                EstimateItem(name="鸡胸肉", portion="130 g", energy="228 kcal", protein="40.3 g", carbs="0.0 g", fat="4.7 g"),
                EstimateItem(name="黄瓜", portion="52 g", energy="8 kcal", protein="0.4 g", carbs="1.5 g", fat="0.1 g"),
                EstimateItem(name="花生米", portion="39 g", energy="221 kcal", protein="10.1 g", carbs="6.3 g", fat="19.2 g"),
            ],
            total_calories="455 kcal",
            suggestion="可适当减少油和花生。",
            itemization_mode="single_dish_ingredients",
        )

        results = split_estimate_by_items(estimate)
        self.assertEqual(len(results), 1)
        self.assertEqual(len(results[0].items), 3)
        self.assertEqual(results[0].itemization_mode, "single_dish_ingredients")


if __name__ == "__main__":
    unittest.main()
