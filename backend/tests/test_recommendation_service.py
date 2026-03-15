import unittest

from backend.schemas.profile import ProfileOut
from backend.services.recommendation import (
    _build_guidance_system_instruction,
    _build_profile_context,
    _parse_guidance_payload,
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
        self.assertIn("Allergies / avoidances: Peanut", context)


if __name__ == "__main__":
    unittest.main()
