import os
import sqlite3
import unittest
from unittest.mock import patch

from backend.database.init_db import init_db
from backend.schemas.profile import ProfileIn
from backend.schemas.user import UserCreate
from backend.services.profile_service import (
    create_profile,
    get_profile,
    get_profile_by_user_id,
    update_profile,
)
from backend.services.user_service import create_user
from backend.tests.test_db_utils import create_workspace_db_path, remove_file_if_exists


class ProfileServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = create_workspace_db_path("profile-service-")
        remove_file_if_exists(self.db_path)
        self.db_patch = patch("backend.database.connection.db_path", self.db_path)
        self.db_patch.start()
        init_db()

        self.user = create_user(
            UserCreate.model_validate(
                {
                    "email": "owner@example.com",
                    "passwordHash": "hashed-password",
                    "displayName": "Owner",
                }
            )
        )
        self.other_user = create_user(
            UserCreate.model_validate(
                {
                    "email": "other@example.com",
                    "passwordHash": "hashed-password",
                    "displayName": "Other",
                }
            )
        )

    def tearDown(self) -> None:
        self.db_patch.stop()
        remove_file_if_exists(self.db_path)

    def test_create_get_and_update_profile_round_trip(self) -> None:
        created = create_profile(self.user.id, build_profile(age=28))

        fetched = get_profile(created.id, self.user.id)
        self.assertIsNotNone(fetched)
        self.assertEqual(fetched.id, created.id)
        self.assertEqual(fetched.allergies, ["Nuts"])
        self.assertEqual(fetched.activity_level, "Lightly active")

        updated = update_profile(created.id, self.user.id, build_profile(age=29, goal="Fat loss"))

        self.assertIsNotNone(updated)
        self.assertEqual(updated.id, created.id)
        self.assertEqual(updated.goal, "Fat loss")

        refetched = get_profile(created.id, self.user.id)
        self.assertIsNotNone(refetched)
        self.assertEqual(refetched.kcal_target, 2400)
        self.assertEqual(refetched.exercise_type, "Strength training")

    def test_profile_lookup_is_scoped_to_user(self) -> None:
        created = create_profile(self.user.id, build_profile())

        self.assertIsNone(get_profile(created.id, self.other_user.id))
        self.assertIsNone(get_profile_by_user_id(self.other_user.id))

    def test_update_profile_returns_none_when_owned_by_other_user(self) -> None:
        created = create_profile(self.user.id, build_profile())

        updated = update_profile(created.id, self.other_user.id, build_profile(goal="Performance"))

        self.assertIsNone(updated)

    def test_create_profile_rejects_second_profile_for_same_user(self) -> None:
        create_profile(self.user.id, build_profile())

        with self.assertRaises(sqlite3.IntegrityError):
            create_profile(self.user.id, build_profile(goal="Performance"))


def build_profile(
    *,
    age: int = 28,
    goal: str = "Muscle gain",
) -> ProfileIn:
    return ProfileIn.model_validate(
        {
            "age": age,
            "height": 178,
            "weight": 72,
            "sex": "Male",
            "activityLevel": "Lightly active",
            "exerciseType": "Strength training",
            "goal": goal,
            "pace": "Moderate",
            "kcalTarget": 2400,
            "dietStyle": "High protein",
            "allergies": ["Nuts"],
        }
    )


if __name__ == "__main__":
    unittest.main()
