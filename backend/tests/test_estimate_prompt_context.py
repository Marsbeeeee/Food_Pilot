import unittest

from backend.schemas.profile import ProfileOut
from backend.services.estimate import (
    _build_estimate_system_instruction,
    _build_profile_context,
)


class EstimatePromptContextTests(unittest.TestCase):
    def test_build_profile_context_contains_key_constraints(self) -> None:
        profile = ProfileOut(
            id=3,
            age=28,
            height=178,
            weight=72,
            sex="Male",
            activity_level="Lightly active",
            exercise_type="Strength training",
            goal="Fat loss",
            pace="Moderate",
            kcal_target=2200,
            diet_style="High protein",
            allergies=["Nuts", "Shellfish"],
        )

        context = _build_profile_context(profile)

        self.assertIn("Goal: Fat loss", context)
        self.assertIn("Daily calorie target: 2200 kcal", context)
        self.assertIn("Diet style: High protein", context)
        self.assertIn("Allergies / avoidances: Nuts, Shellfish", context)

    def test_system_instruction_includes_profile_context_when_available(self) -> None:
        system_instruction = _build_estimate_system_instruction(
            "Base prompt",
            "User profile:\n- Goal: Fat loss",
        )

        self.assertIn("Base prompt", system_instruction)
        self.assertIn("Use the following user profile context", system_instruction)
        self.assertIn("Goal: Fat loss", system_instruction)
        self.assertIn("Do not recommend foods", system_instruction)

    def test_system_instruction_stays_default_without_profile_context(self) -> None:
        system_instruction = _build_estimate_system_instruction("Base prompt", None)

        self.assertIn("Base prompt", system_instruction)
        self.assertNotIn("Use the following user profile context", system_instruction)

    def test_system_instruction_includes_food_knowledge_context_when_available(self) -> None:
        system_instruction = _build_estimate_system_instruction(
            "Base prompt",
            None,
            food_knowledge_context="Chinese food knowledge context: 牛肉面 每100g 132 kcal",
        )

        self.assertIn("Base prompt", system_instruction)
        self.assertIn("Chinese food knowledge context", system_instruction)
        self.assertIn("牛肉面", system_instruction)


if __name__ == "__main__":
    unittest.main()
