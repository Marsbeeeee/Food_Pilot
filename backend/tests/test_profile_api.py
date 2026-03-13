import os
import tempfile
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.database.init_db import init_db
from backend.routers.profile import router as profile_router


class ProfileApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_foodpilot.db")
        self.db_patch = patch("backend.database.connection.db_path", self.db_path)
        self.db_patch.start()
        init_db()

        app = FastAPI()
        app.include_router(profile_router)
        self.client = TestClient(app)

    def tearDown(self) -> None:
        self.db_patch.stop()
        self.temp_dir.cleanup()

    def test_profile_crud_routes_return_expected_status_codes(self) -> None:
        create_response = self.client.post(
            "/profile",
            json={
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
            },
        )

        self.assertEqual(create_response.status_code, 201)
        created_payload = create_response.json()
        profile_id = created_payload["id"]
        self.assertEqual(created_payload["activityLevel"], "轻度活动")
        self.assertEqual(created_payload["allergies"], ["坚果"])

        get_response = self.client.get(f"/profile/{profile_id}")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json()["id"], profile_id)

        update_response = self.client.put(
            f"/profile/{profile_id}",
            json={
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
            },
        )

        self.assertEqual(update_response.status_code, 200)
        updated_payload = update_response.json()
        self.assertEqual(updated_payload["goal"], "减脂")
        self.assertEqual(updated_payload["allergies"], ["海鲜"])

    def test_missing_profile_returns_404(self) -> None:
        get_response = self.client.get("/profile/999")
        self.assertEqual(get_response.status_code, 404)
        self.assertEqual(get_response.json()["detail"], "Profile not found")

        update_response = self.client.put(
            "/profile/999",
            json={
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
            },
        )
        self.assertEqual(update_response.status_code, 404)
        self.assertEqual(update_response.json()["detail"], "Profile not found")

    def test_invalid_profile_payload_returns_422(self) -> None:
        create_response = self.client.post(
            "/profile",
            json={
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
            },
        )
        self.assertEqual(create_response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
