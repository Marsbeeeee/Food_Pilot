import unittest

from backend.schemas.profile import ProfileIn, ProfileOut


class ProfileSchemaTests(unittest.TestCase):
    def test_profile_in_accepts_camel_case_contract(self) -> None:
        profile = ProfileIn.model_validate(
            {
                "age": 28,
                "height": 178,
                "weight": 72,
                "sex": "男",
                "activityLevel": "轻度活动",
                "exerciseType": "混合运动",
                "goal": "增肌",
                "pace": "适中",
                "kcalTarget": 2400,
                "dietStyle": "高蛋白饮食",
                "allergies": ["坚果", "海鲜"],
            }
        )

        self.assertEqual(profile.activity_level, "轻度活动")
        self.assertEqual(profile.exercise_type, "混合运动")
        self.assertEqual(profile.kcal_target, 2400)
        self.assertEqual(profile.diet_style, "高蛋白饮食")
        self.assertEqual(profile.allergies, ["坚果", "海鲜"])

    def test_profile_out_serializes_back_to_camel_case(self) -> None:
        profile = ProfileOut(
            id=1,
            age=28,
            height=178,
            weight=72,
            sex="男",
            activity_level="轻度活动",
            exercise_type="混合运动",
            goal="增肌",
            pace="适中",
            kcal_target=2400,
            diet_style="高蛋白饮食",
            allergies='["坚果"]',
        )

        payload = profile.model_dump(by_alias=True)

        self.assertIn("activityLevel", payload)
        self.assertIn("exerciseType", payload)
        self.assertIn("kcalTarget", payload)
        self.assertIn("dietStyle", payload)
        self.assertNotIn("activity_level", payload)
        self.assertEqual(payload["allergies"], ["坚果"])


if __name__ == "__main__":
    unittest.main()
