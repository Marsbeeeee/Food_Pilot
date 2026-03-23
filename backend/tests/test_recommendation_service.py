import unittest

from backend.schemas.profile import ProfileOut
from backend.services.recommendation import (
    _build_guidance_system_instruction,
    _build_profile_context,
    _parse_guidance_payload,
    check_allergen_violations,
)


class RecommendationServiceTests(unittest.TestCase):
    def test_parse_guidance_payload_uses_chinese_defaults_for_recommendation(self) -> None:
        result = _parse_guidance_payload(
            {
                "response": "晚饭优先选鸡肉沙拉，再补一份玉米汤，会更稳妥。",
            },
            response_mode="meal_recommendation",
        )

        self.assertEqual(result.title, "餐食推荐")
        self.assertEqual(result.description, "这是基于你当前问题给出的推荐建议。")
        self.assertEqual(result.response, "晚饭优先选鸡肉沙拉，再补一份玉米汤，会更稳妥。")

    def test_parse_guidance_payload_uses_auxiliary_defaults_for_text(self) -> None:
        result = _parse_guidance_payload(
            {
                "response": "更推荐烤鸡，是因为它通常更容易控制油脂和总热量。",
            },
            response_mode="text",
        )

        self.assertEqual(result.title, "补充说明")
        self.assertEqual(result.description, "这是对当前问题的补充说明。")
        self.assertEqual(result.response, "更推荐烤鸡，是因为它通常更容易控制油脂和总热量。")

    def test_parse_guidance_payload_accepts_common_aliases(self) -> None:
        result = _parse_guidance_payload(
            {
                "name": "晚餐怎么选",
                "reason": "鸡肉沙拉脂肪更低，也更容易控制总量。",
                "choice": "如果你今晚想吃得轻一点，优先选鸡肉沙拉；如果还想更饱，可以加一份南瓜汤。",
            },
            response_mode="meal_recommendation",
        )

        self.assertEqual(result.title, "晚餐怎么选")
        self.assertEqual(result.description, "鸡肉沙拉脂肪更低，也更容易控制总量。")
        self.assertIn("优先选鸡肉沙拉", result.response)

    def test_build_guidance_system_instruction_for_recommendation_emphasizes_choice_and_reason(self) -> None:
        system_instruction = _build_guidance_system_instruction(
            response_mode="meal_recommendation",
            profile_context=None,
        )

        self.assertIn("Reply in Simplified Chinese.", system_instruction)
        self.assertIn("give the user a concrete choice or direction first", system_instruction)
        self.assertIn("Do not turn recommendation requests into calorie-estimate tables", system_instruction)
        self.assertIn("Do not output calorie tables", system_instruction)

    def test_build_guidance_system_instruction_for_text_keeps_auxiliary_scope(self) -> None:
        system_instruction = _build_guidance_system_instruction(
            response_mode="text",
            profile_context=None,
        )

        self.assertIn("auxiliary fallback", system_instruction)
        self.assertIn("Do not expand text requests into a third complex capability", system_instruction)

    def test_build_guidance_system_instruction_includes_food_knowledge_context_when_available(self) -> None:
        system_instruction = _build_guidance_system_instruction(
            response_mode="meal_recommendation",
            profile_context=None,
            food_knowledge_context="Chinese food knowledge context: 珍珠奶茶 每100g 88 kcal",
        )

        self.assertIn("Chinese food knowledge context", system_instruction)
        self.assertIn("珍珠奶茶", system_instruction)

    def test_build_profile_context_contains_constraints(self) -> None:
        profile = ProfileOut(
            id=8,
            age=29,
            height=168,
            weight=60,
            sex="Female",
            activity_level="Moderately active",
            exercise_type="Pilates",
            goal="Fat loss",
            pace="Moderate",
            kcal_target=1800,
            diet_style="Balanced",
            allergies=["Peanut"],
        )

        context = _build_profile_context(profile)

        self.assertIn("Goal: Fat loss", context)
        self.assertIn("Daily calorie target: 1800 kcal", context)
        self.assertIn("Peanut", context)

    def test_check_allergen_violations_reports_allergens_in_nested_structures(self) -> None:
        ok, violations = check_allergen_violations(
            {
                "title": "晚餐推荐",
                "description": "推荐鸡肉沙拉搭配一小把花生作为零食。",
                "options": [
                    "鸡肉沙拉 + 花生",
                    "清炒西兰花",
                ],
            },
            allergens=["花生", "牛奶"],
        )

        self.assertFalse(ok)
        self.assertIn("花生", violations)
        self.assertNotIn("牛奶", violations)

    def test_check_allergen_violations_is_ok_when_no_allergens_present(self) -> None:
        ok, violations = check_allergen_violations(
            ["鸡肉沙拉", "清炒西兰花"],
            allergens=["花生"],
        )

        self.assertTrue(ok)
        self.assertEqual(violations, [])


if __name__ == "__main__":
    unittest.main()
