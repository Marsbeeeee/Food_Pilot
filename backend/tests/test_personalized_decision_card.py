import unittest

from backend.schemas.decision_card import build_decision_card_from_estimate
from backend.schemas.profile import ProfileOut


class PersonalizedDecisionCardTests(unittest.TestCase):
    def test_same_milk_tea_differs_between_fat_loss_and_muscle_gain_profiles(self) -> None:
        fat_loss_profile = ProfileOut.model_validate(
            {
                "id": 1,
                "age": 27,
                "height": 168,
                "weight": 58,
                "sex": "Female",
                "activityLevel": "Lightly active",
                "exerciseType": "Walking",
                "goal": "Fat loss",
                "pace": "Moderate",
                "kcalTarget": 1800,
                "dietStyle": "Balanced",
                "allergies": [],
            }
        )
        muscle_gain_profile = ProfileOut.model_validate(
            {
                "id": 2,
                "age": 27,
                "height": 178,
                "weight": 72,
                "sex": "Male",
                "activityLevel": "Moderately active",
                "exerciseType": "Strength training",
                "goal": "Muscle gain",
                "pace": "Moderate",
                "kcalTarget": 2600,
                "dietStyle": "Balanced",
                "allergies": [],
            }
        )

        fat_loss_card = build_decision_card_from_estimate(
            input_summary="霸王茶姬 伯牙绝弦 大杯 三分糖",
            title="伯牙绝弦",
            confidence="high",
            description="现制茶饮。",
            items=[{"name": "奶茶", "portion": "1 杯", "energy": "310 kcal"}],
            total_calories="310 kcal",
            suggestion="可按目标调整糖度。",
            container_type="chat_message",
            profile=fat_loss_profile,
            profile_requested=True,
        )
        muscle_gain_card = build_decision_card_from_estimate(
            input_summary="霸王茶姬 伯牙绝弦 大杯 三分糖",
            title="伯牙绝弦",
            confidence="high",
            description="现制茶饮。",
            items=[{"name": "奶茶", "portion": "1 杯", "energy": "310 kcal"}],
            total_calories="310 kcal",
            suggestion="可按目标调整糖度。",
            container_type="chat_message",
            profile=muscle_gain_profile,
            profile_requested=True,
        )

        self.assertTrue(fat_loss_card.is_personalized)
        self.assertTrue(muscle_gain_card.is_personalized)
        self.assertEqual(fat_loss_card.recommendation_level, "caution")
        self.assertEqual(muscle_gain_card.recommendation_level, "acceptable")
        self.assertIn("high_sugar", fat_loss_card.risk_tags)
        self.assertIn("low_protein", muscle_gain_card.risk_tags)
        self.assertNotEqual(fat_loss_card.adaptation_note, muscle_gain_card.adaptation_note)

    def test_allergen_conflict_prioritizes_safety_block(self) -> None:
        allergy_profile = ProfileOut.model_validate(
            {
                "id": 3,
                "age": 30,
                "height": 170,
                "weight": 65,
                "sex": "Male",
                "activityLevel": "Moderately active",
                "exerciseType": "Running",
                "goal": "Fat loss",
                "pace": "Moderate",
                "kcalTarget": 1900,
                "dietStyle": "Balanced",
                "allergies": ["花生"],
            }
        )

        decision_card = build_decision_card_from_estimate(
            input_summary="花生酱吐司",
            title="花生酱吐司",
            confidence="high",
            description="吐司配花生酱。",
            items=[{"name": "花生酱吐司", "portion": "2 片", "energy": "360 kcal"}],
            total_calories="360 kcal",
            suggestion="不适合花生过敏场景。",
            container_type="estimate_api",
            profile=allergy_profile,
            profile_requested=True,
        )

        self.assertEqual(decision_card.recommendation_level, "not_recommended")
        self.assertIn("allergen_conflict", decision_card.risk_tags)
        self.assertTrue(any("花生" in item for item in decision_card.adjustments))
        self.assertTrue(decision_card.alternatives)

    def test_missing_profile_falls_back_to_generic_conclusion(self) -> None:
        decision_card = build_decision_card_from_estimate(
            input_summary="霸王茶姬 伯牙绝弦 大杯 三分糖",
            title="伯牙绝弦",
            confidence="high",
            description="现制茶饮。",
            items=[{"name": "奶茶", "portion": "1 杯", "energy": "310 kcal"}],
            total_calories="310 kcal",
            suggestion="可按目标调整糖度。",
            container_type="chat_message",
            profile=None,
            profile_requested=False,
        )

        self.assertFalse(decision_card.is_personalized)
        self.assertEqual(decision_card.personalization_note, "未提供 Profile，当前为通用结论。")
        self.assertIn(decision_card.recommendation_level, {"acceptable", "caution"})
        self.assertIn("high_sugar", decision_card.risk_tags)


if __name__ == "__main__":
    unittest.main()
