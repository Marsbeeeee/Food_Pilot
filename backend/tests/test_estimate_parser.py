import unittest

from backend.services.estimate_parser import parse_estimate_payload


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


if __name__ == "__main__":
    unittest.main()
