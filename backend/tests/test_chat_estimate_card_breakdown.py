import unittest
from unittest.mock import patch

from backend.schemas.estimate import EstimateItem, EstimateResult
from backend.services.estimate_parser import split_estimate_by_items


class ChatEstimateCardBreakdownTests(unittest.TestCase):
    def test_split_estimate_by_items_expands_each_card_components_when_query_mentions_multiple_dishes(self) -> None:
        estimate = EstimateResult(
            title="午餐估算",
            description="两道菜的组合估算",
            confidence="高",
            items=[
                EstimateItem(
                    name="辣椒炒肉",
                    portion="约200g",
                    energy="290 kcal",
                    protein="18.5 g",
                    carbs="6.2 g",
                    fat="19.2 g",
                ),
                EstimateItem(
                    name="白米饭",
                    portion="小碗约150g",
                    energy="174 kcal",
                    protein="3.9 g",
                    carbs="38.9 g",
                    fat="0.5 g",
                ),
            ],
            total_calories="464 kcal",
            suggestion="这餐碳水和脂肪都不低。",
        )

        with patch(
            "backend.services.estimate_parser.build_single_dish_ingredient_breakdown",
            side_effect=[
                [
                    {"name": "瘦猪肉", "portion": "100 g", "energy": "143 kcal", "protein": "20.3 g", "fat": "6.2 g"},
                    {"name": "青红椒", "portion": "100 g", "energy": "19 kcal", "carbs": "4.1 g"},
                    {"name": "烹调用油", "portion": "8 g", "energy": "72 kcal", "fat": "8.0 g"},
                ],
                None,
            ],
        ):
            cards = split_estimate_by_items(
                estimate,
                query="我中午吃了辣椒炒肉和白米饭估算热量",
            )

        self.assertEqual(len(cards), 2)
        self.assertEqual(cards[0].title, "辣椒炒肉")
        self.assertEqual(cards[0].itemization_mode, "single_dish_ingredients")
        self.assertEqual(len(cards[0].items), 3)
        self.assertEqual(cards[0].items[0].name, "瘦猪肉")
        self.assertEqual(cards[1].title, "白米饭")
        self.assertIsNone(cards[1].itemization_mode)
        self.assertEqual(len(cards[1].items), 1)
        self.assertEqual(cards[1].items[0].name, "白米饭")


if __name__ == "__main__":
    unittest.main()
