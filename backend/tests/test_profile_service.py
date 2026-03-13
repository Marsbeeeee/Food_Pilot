import os
import tempfile
import unittest
from unittest.mock import patch

from backend.database.init_db import init_db
from backend.schemas.profile import ProfileIn
from backend.services.profile_service import (
    create_profile,
    get_profile,
    update_profile,
)


class ProfileServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_foodpilot.db")
        self.db_patch = patch("backend.database.connection.db_path", self.db_path)
        self.db_patch.start()
        init_db()

    def tearDown(self) -> None:
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def test_create_get_and_update_profile_round_trip(self) -> None:
        created = create_profile(
            ProfileIn.model_validate(
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
                    "allergies": ["坚果"],
                }
            )
        )

        fetched = get_profile(created.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, created.id)
        self.assertEqual(fetched.allergies, ["坚果"])
        self.assertEqual(fetched.activity_level, "轻度活动")

        updated = update_profile(
            created.id,
            ProfileIn.model_validate(
                {
                    "age": 29,
                    "height": 178,
                    "weight": 73,
                    "sex": "男",
                    "activityLevel": "中度活动",
                    "exerciseType": "力量训练",
                    "goal": "减脂",
                    "pace": "积极",
                    "kcalTarget": 2200,
                    "dietStyle": "均衡饮食",
                    "allergies": ["海鲜"],
                }
            ),
        )

        self.assertIsNotNone(updated)
        self.assertEqual(updated.id, created.id)
        self.assertEqual(updated.goal, "减脂")
        self.assertEqual(updated.allergies, ["海鲜"])

        refetched = get_profile(created.id)
        self.assertIsNotNone(refetched)
        self.assertEqual(refetched.kcal_target, 2200)
        self.assertEqual(refetched.exercise_type, "力量训练")

    def test_get_profile_returns_none_when_missing(self) -> None:
        self.assertIsNone(get_profile(999))

    def test_update_profile_returns_none_when_missing(self) -> None:
        updated = update_profile(
            999,
            ProfileIn.model_validate(
                {
                    "age": 29,
                    "height": 178,
                    "weight": 73,
                    "sex": "男",
                    "activityLevel": "中度活动",
                    "exerciseType": "力量训练",
                    "goal": "减脂",
                    "pace": "积极",
                    "kcalTarget": 2200,
                    "dietStyle": "均衡饮食",
                    "allergies": [],
                }
            ),
        )
        self.assertIsNone(updated)


if __name__ == "__main__":
    unittest.main()
