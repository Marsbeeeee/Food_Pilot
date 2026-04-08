import unittest

from backend.services.brand_estimation import _validate_estimation_config, resolve_brand_estimation


class BrandEstimationTests(unittest.TestCase):
    def test_brand_template_hit_returns_high_confidence_snapshot(self) -> None:
        result = resolve_brand_estimation(
            input_summary="霸王茶姬 伯牙绝弦 大杯 三分糖",
            title="伯牙绝弦",
            items=[{"name": "奶茶", "portion": "1 杯", "energy": "300 kcal"}],
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["confidence"], "high")
        self.assertEqual(result["title"], "霸王茶姬 伯牙绝弦")
        self.assertEqual(result["estimation_meta"]["source_type"], "brand_template")
        self.assertEqual(result["estimation_meta"]["source_label"], "霸王茶姬 / 伯牙绝弦")
        self.assertEqual(result["estimation_meta"]["fallback_path"], ["brand_template"])
        self.assertEqual(result["estimation_meta"]["template_version"], "v1")
        self.assertEqual(result["estimation_meta"]["config_version"], "task8.v2026-04-08")
        self.assertEqual(result["items"][0]["portion"], "大杯 1 杯")

    def test_brand_template_applies_sugar_and_addon_modifiers(self) -> None:
        baseline = resolve_brand_estimation(
            input_summary="霸王茶姬 伯牙绝弦 大杯 三分糖",
            title="伯牙绝弦",
            items=[{"name": "奶茶", "portion": "1 杯", "energy": "300 kcal"}],
        )
        adjusted = resolve_brand_estimation(
            input_summary="霸王茶姬 伯牙绝弦 大杯 全糖 加珍珠",
            title="伯牙绝弦",
            items=[{"name": "奶茶", "portion": "1 杯", "energy": "300 kcal"}],
        )

        self.assertIsNotNone(baseline)
        self.assertIsNotNone(adjusted)
        assert baseline is not None
        assert adjusted is not None
        baseline_total = int(str(baseline["total_calories"]).split()[0])
        adjusted_total = int(str(adjusted["total_calories"]).split()[0])

        self.assertGreater(adjusted_total, baseline_total)
        self.assertTrue(
            any("糖度：全糖" in rule for rule in adjusted["estimation_meta"]["applied_rules"])
        )
        self.assertTrue(
            any("加珍珠" in rule for rule in adjusted["estimation_meta"]["applied_rules"])
        )

    def test_category_template_fallback_marks_medium_confidence(self) -> None:
        result = resolve_brand_estimation(
            input_summary="珍珠奶茶 少糖",
            title="珍珠奶茶",
            items=[{"name": "奶茶", "portion": "1 杯", "energy": "280 kcal"}],
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["confidence"], "medium")
        self.assertEqual(result["estimation_meta"]["source_type"], "category_template")
        self.assertEqual(
            result["estimation_meta"]["fallback_path"],
            ["brand_template", "category_template"],
        )

    def test_generic_template_fallback_marks_low_confidence_and_missing_config(self) -> None:
        result = resolve_brand_estimation(
            input_summary="奶茶 去冰",
            title="奶茶",
            items=[{"name": "奶茶", "portion": "1 杯", "energy": "260 kcal"}],
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["confidence"], "low")
        self.assertEqual(result["estimation_meta"]["source_type"], "generic_template")
        self.assertIn("sugar_level", result["estimation_meta"]["missing_configuration"])
        self.assertEqual(
            result["estimation_meta"]["fallback_path"],
            ["brand_template", "category_template", "generic_template"],
        )

    def test_new_high_frequency_brand_templates_are_available(self) -> None:
        result = resolve_brand_estimation(
            input_summary="喜茶 多肉葡萄 大杯 少糖",
            title="多肉葡萄",
            items=[{"name": "果茶", "portion": "1 杯", "energy": "240 kcal"}],
        )

        self.assertIsNotNone(result)
        assert result is not None
        self.assertEqual(result["confidence"], "high")
        self.assertEqual(result["estimation_meta"]["source_type"], "brand_template")
        self.assertEqual(result["estimation_meta"]["source_label"], "喜茶 / 多肉葡萄")
        self.assertEqual(result["estimation_meta"]["template_id"], "brand.heytea.duorou_grape.v1")

    def test_config_validation_rejects_duplicate_template_ids(self) -> None:
        with self.assertRaisesRegex(ValueError, "duplicate template_id"):
            _validate_estimation_config(
                {
                    "config_version": "broken.v1",
                    "fallback_order": [
                        "brand_template",
                        "category_template",
                        "generic_template",
                    ],
                    "templates": {
                        "brand": [
                            {
                                "template_id": "brand.duplicate.v1",
                                "template_version": "v1",
                                "source_type": "brand_template",
                                "source_label": "测试品牌 / 测试商品",
                                "brand_id": "demo",
                                "category_id": "tea_drink",
                                "nutrition": {
                                    "calories": 100.0,
                                    "protein": 1.0,
                                    "carbs": 10.0,
                                    "fat": 1.0,
                                },
                            },
                            {
                                "template_id": "brand.duplicate.v1",
                                "template_version": "v1",
                                "source_type": "brand_template",
                                "source_label": "测试品牌 / 测试商品二",
                                "brand_id": "demo",
                                "category_id": "tea_drink",
                                "nutrition": {
                                    "calories": 120.0,
                                    "protein": 2.0,
                                    "carbs": 12.0,
                                    "fat": 2.0,
                                },
                            },
                        ],
                        "category": [],
                        "generic": [],
                    },
                    "modifiers": {},
                }
            )


if __name__ == "__main__":
    unittest.main()
