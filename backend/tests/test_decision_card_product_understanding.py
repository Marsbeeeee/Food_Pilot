import unittest

from backend.schemas.decision_card import (
    build_clarification_decision_card,
    build_decision_card_from_estimate,
)


class DecisionCardProductUnderstandingTests(unittest.TestCase):
    def test_build_decision_card_enriches_branded_drink_product_understanding(self) -> None:
        decision_card = build_decision_card_from_estimate(
            input_summary="霸王茶姬 伯牙绝弦 大杯 三分糖",
            title="伯牙绝弦",
            confidence="high",
            description="现制茶饮。",
            items=[
                {
                    "name": "奶茶",
                    "portion": "1 杯",
                    "energy": "310 kcal",
                }
            ],
            total_calories="310 kcal",
            suggestion="减脂期建议少糖。",
            container_type="chat_message",
        )

        self.assertEqual(decision_card.confidence_level, "high")
        self.assertFalse(decision_card.needs_clarification)
        self.assertEqual(decision_card.normalized_product.brand_name, "霸王茶姬")
        self.assertEqual(decision_card.normalized_product.category_name, "现制茶饮")
        self.assertEqual(decision_card.normalized_product.product_name, "伯牙绝弦")
        self.assertEqual(decision_card.normalized_product.normalized_name, "伯牙绝弦")
        self.assertEqual(decision_card.normalized_product.size_or_spec, "大杯")
        self.assertEqual(decision_card.normalized_product.sugar_level, "三分糖")
        self.assertEqual(decision_card.normalized_product.match_level, "brand_product")
        self.assertEqual(decision_card.normalized_product.missing_fields, [])
        self.assertTrue(decision_card.analysis_eligible)

    def test_build_decision_card_detects_combo_scope_from_multi_item_estimate(self) -> None:
        decision_card = build_decision_card_from_estimate(
            input_summary="麦当劳 双人套餐 汉堡 薯条 可乐",
            title="双人套餐",
            confidence="medium",
            description="快餐套餐。",
            items=[
                {
                    "name": "汉堡",
                    "portion": "2 个",
                    "energy": "500 kcal",
                },
                {
                    "name": "薯条",
                    "portion": "2 份",
                    "energy": "420 kcal",
                },
                {
                    "name": "可乐",
                    "portion": "2 杯",
                    "energy": "300 kcal",
                },
            ],
            total_calories="1220 kcal",
            suggestion="如果要更稳妥，可以把可乐换成无糖饮料。",
            container_type="chat_message",
        )

        self.assertEqual(decision_card.normalized_product.product_scope, "multi_item")
        self.assertEqual(len(decision_card.normalized_product.combo_items), 3)
        self.assertEqual(decision_card.normalized_product.combo_items[0].item_role, "main_item")
        self.assertIn(
            decision_card.normalized_product.combo_items[1].item_role,
            {"combo_item", "combo_side"},
        )

    def test_build_clarification_decision_card_exposes_missing_fields_for_brand_only_input(self) -> None:
        decision_card = build_clarification_decision_card(
            input_summary="麦当劳汉堡",
            container_type="chat_message",
            reason="missing_product_detail",
        )

        self.assertTrue(decision_card.needs_clarification)
        self.assertEqual(decision_card.confidence_level, "low")
        self.assertIn("missing_product_detail", decision_card.risk_tags)
        self.assertIn("product_name", decision_card.normalized_product.missing_fields)
        self.assertEqual(decision_card.normalized_product.brand_name, "麦当劳")
        self.assertEqual(decision_card.normalized_product.match_level, "brand_only")
        self.assertGreaterEqual(len(decision_card.adjustments), 1)


if __name__ == "__main__":
    unittest.main()
