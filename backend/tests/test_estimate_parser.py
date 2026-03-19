import unittest

from backend.schemas.estimate import EstimateItem, EstimateResult
from backend.services.estimate_parser import parse_estimate_payload, split_estimate_by_items


class EstimateParserTests(unittest.TestCase):
    def test_parse_estimate_payload_uses_chinese_defaults_for_optional_fields(self) -> None:
        result = parse_estimate_payload(
            {
                "items": [
                    {
                        "name": "鸡胸肉",
                        "portion": "150g",
                        "energy": "240 kcal",
                    }
                ],
                "total_calories": "240 kcal",
            }
        )

        self.assertEqual(result.title, "餐食营养估算")
        self.assertEqual(result.description, "这是根据你的描述给出的热量和营养大致拆解。")
        self.assertEqual(result.confidence, "中")
        self.assertEqual(result.suggestion, "如果补充份量、做法或食材细节，估算会更准确。")

    def test_parse_estimate_payload_accepts_common_aliases_and_fills_missing_portion(self) -> None:
        result = parse_estimate_payload(
            {
                "mealTitle": "午餐估算",
                "summary": "一份常见中式午餐的估算。",
                "certainty": "高",
                "items": [
                    {
                        "ingredient": "米饭",
                        "amount": "1 碗",
                        "calories": "230 kcal",
                    },
                    {
                        "title": "宫保鸡丁",
                        "kcal": "320 kcal",
                    },
                    {
                        "ingredient": "",
                        "calories": "50 kcal",
                    },
                ],
                "totalEnergy": "550 kcal",
                "advice": "如果少放一点油，热量会更低。",
            }
        )

        self.assertEqual(result.title, "午餐估算")
        self.assertEqual(result.description, "一份常见中式午餐的估算。")
        self.assertEqual(result.confidence, "高")
        self.assertEqual(result.total_calories, "550 kcal")
        self.assertEqual(result.suggestion, "如果少放一点油，热量会更低。")
        self.assertEqual(len(result.items), 2)
        self.assertEqual(result.items[0].name, "米饭")
        self.assertEqual(result.items[0].portion, "1 碗")
        self.assertEqual(result.items[1].name, "宫保鸡丁")
        self.assertEqual(result.items[1].portion, "未说明")
        self.assertEqual(result.items[1].energy, "320 kcal")

    def test_parse_estimate_payload_requires_at_least_one_valid_item(self) -> None:
        with self.assertRaises(ValueError) as context:
            parse_estimate_payload(
                {
                    "items": [
                        {
                            "name": "炒面",
                            "portion": "1 盘",
                        }
                    ],
                    "total": "480 kcal",
                }
            )

        self.assertEqual(str(context.exception), "AI response is missing item details")

    def test_split_estimate_by_items_returns_single_when_one_item(self) -> None:
        estimate = EstimateResult(
            title="包子",
            description="常见中式早餐",
            confidence="中",
            items=[EstimateItem(name="猪肉白菜包子", portion="2个", energy="360 kcal", protein="14.0 g", carbs="52.0 g", fat="12.0 g")],
            total_calories="360 kcal",
            suggestion="补充份量更准确。",
        )
        results = split_estimate_by_items(estimate)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0].title, "包子")
        self.assertEqual(len(results[0].items), 1)

    def test_split_estimate_by_items_splits_multiple_foods(self) -> None:
        estimate = EstimateResult(
            title="中式早餐",
            description="常见中式早餐组合",
            confidence="中",
            items=[
                EstimateItem(name="猪肉白菜包子", portion="2个", energy="360 kcal", protein="14.0 g", carbs="52.0 g", fat="12.0 g"),
                EstimateItem(name="无糖豆浆", portion="1杯", energy="80 kcal", protein="7.5 g", carbs="4.0 g", fat="3.5 g"),
            ],
            total_calories="440 kcal",
            suggestion="如果补充份量、做法或食材细节，估算会更准确。",
        )
        results = split_estimate_by_items(estimate)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0].title, "猪肉白菜包子")
        self.assertEqual(results[0].total_calories, "360 kcal")
        self.assertEqual(len(results[0].items), 1)
        self.assertEqual(results[1].title, "无糖豆浆")
        self.assertEqual(results[1].total_calories, "80 kcal")
        self.assertEqual(len(results[1].items), 1)


if __name__ == "__main__":
    unittest.main()
