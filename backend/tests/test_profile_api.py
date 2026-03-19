import os
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.database.init_db import init_db
from backend.dependencies.auth import get_current_user
from backend.routers.profile import router as profile_router
from backend.schemas.user import UserCreate
from backend.schemas.user import UserOut
from backend.services.user_service import create_user
from backend.tests.test_db_utils import create_workspace_db_path, remove_file_if_exists


class ProfileApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = create_workspace_db_path("profile-api-")
        remove_file_if_exists(self.db_path)
        self.db_patch = patch("backend.database.connection.db_path", self.db_path)
        self.db_patch.start()
        init_db()
        create_user(
            UserCreate.model_validate(
                {
                    "email": "owner@example.com",
                    "passwordHash": "hashed-password",
                    "displayName": "Owner",
                }
            )
        )

        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: UserOut.model_validate(
            {
                "id": 1,
                "email": "owner@example.com",
                "display_name": "Owner",
                "created_at": "2026-03-13 18:00:00",
                "updated_at": "2026-03-13 18:00:00",
            }
        )
        app.include_router(profile_router)
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.db_patch.stop()
        remove_file_if_exists(self.db_path)

    def test_profile_crud_routes_return_expected_status_codes(self) -> None:
        create_response = self.client.post(
            "/profile",
            json=build_payload(),
        )

        self.assertEqual(create_response.status_code, 201)
        created_payload = create_response.json()
        profile_id = created_payload["id"]
        self.assertEqual(created_payload["activityLevel"], "Lightly active")
        self.assertEqual(created_payload["allergies"], ["Nuts"])

        get_me_response = self.client.get("/profile/me")
        self.assertEqual(get_me_response.status_code, 200)
        self.assertEqual(get_me_response.json()["id"], profile_id)

        get_response = self.client.get(f"/profile/{profile_id}")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json()["id"], profile_id)

        update_response = self.client.put(
            f"/profile/{profile_id}",
            json=build_payload(age=29, goal="Fat loss", allergies=["Seafood"]),
        )

        self.assertEqual(update_response.status_code, 200)
        updated_payload = update_response.json()
        self.assertEqual(updated_payload["goal"], "Fat loss")
        self.assertEqual(updated_payload["allergies"], ["Seafood"])

    def test_missing_profile_returns_404(self) -> None:
        get_response = self.client.get("/profile/me")
        self.assertEqual(get_response.status_code, 404)
        self.assertEqual(get_response.json()["detail"], "Profile not found")

    def test_duplicate_profile_returns_409(self) -> None:
        self.client.post("/profile", json=build_payload())
        duplicate_response = self.client.post("/profile", json=build_payload())

        self.assertEqual(duplicate_response.status_code, 409)
        self.assertEqual(duplicate_response.json()["detail"], "Profile already exists")


def build_payload(
    *,
    age: int = 28,
    goal: str = "Muscle gain",
    allergies: list[str] | None = None,
) -> dict:
    return {
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
        "allergies": allergies or ["Nuts"],
    }


if __name__ == "__main__":
    unittest.main()
