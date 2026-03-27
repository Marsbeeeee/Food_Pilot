import os
import unittest
from unittest.mock import patch

from fastapi import FastAPI
from fastapi.testclient import TestClient

from backend.database.connection import get_db_connection
from backend.database.init_db import init_db
from backend.dependencies.auth import get_current_user
from backend.repositories.standard_dish_repository import (
    approve_dish_image_candidate,
    create_dish_image_candidate,
    get_or_create_standard_dish,
    get_standard_dish_by_id,
)
from backend.routers.admin_dish_images import router as admin_dish_images_router
from backend.schemas.user import UserCreate, UserOut
from backend.services.user_service import create_user
from backend.tests.test_db_utils import create_workspace_db_path, remove_file_if_exists


class AdminDishImageApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = create_workspace_db_path("admin-dish-image-api-")
        remove_file_if_exists(self.db_path)
        self.db_patch = patch("backend.database.connection.db_path", self.db_path)
        self.db_patch.start()
        with patch.dict(os.environ, {"ADMIN_EMAILS": "admin@example.com"}):
            init_db()
            self.admin_user = create_user(
                UserCreate.model_validate(
                    {
                        "email": "admin@example.com",
                        "passwordHash": "hashed-password",
                        "displayName": "Admin",
                    }
                )
            )
        self.normal_user = create_user(
            UserCreate.model_validate(
                {
                    "email": "member@example.com",
                    "passwordHash": "hashed-password",
                    "displayName": "Member",
                }
            )
        )

    def tearDown(self) -> None:
        self.db_patch.stop()
        remove_file_if_exists(self.db_path)

    def test_non_admin_cannot_access_review_console_routes(self) -> None:
        client = self._build_client(self.normal_user)

        response = client.get("/admin/dish-images")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["detail"], "Admin access required")

    def test_admin_can_list_candidates_with_status_and_query_filters(self) -> None:
        conn = get_db_connection()
        try:
            pending_dish = get_or_create_standard_dish(conn, "宫保鸡丁")
            create_dish_image_candidate(
                conn,
                int(pending_dish["id"]),
                image_url="https://img.example/kungpao-pending.jpg",
                prompt_version="v1",
            )
            approved_dish = get_or_create_standard_dish(conn, "番茄炒蛋")
            approved_candidate = create_dish_image_candidate(
                conn,
                int(approved_dish["id"]),
                image_url="https://img.example/tomato-approved.jpg",
                prompt_version="v1",
            )
            approve_dish_image_candidate(
                conn,
                int(approved_dish["id"]),
                int(approved_candidate["id"]),
                reviewed_by_user_id=self.admin_user.id,
            )
        finally:
            conn.close()

        client = self._build_client(self.admin_user)

        pending_response = client.get("/admin/dish-images", params={"status": "pending", "query": "宫保"})
        approved_response = client.get("/admin/dish-images", params={"status": "approved"})

        self.assertEqual(pending_response.status_code, 200)
        self.assertEqual(len(pending_response.json()), 1)
        self.assertEqual(pending_response.json()[0]["standardDishName"], "宫保鸡丁")

        self.assertEqual(approved_response.status_code, 200)
        self.assertEqual(len(approved_response.json()), 1)
        self.assertEqual(approved_response.json()[0]["standardDishName"], "番茄炒蛋")
        self.assertTrue(approved_response.json()[0]["isCurrentOfficial"])

    def test_admin_can_approve_candidate_and_audit_event_is_returned(self) -> None:
        conn = get_db_connection()
        try:
            standard_dish = get_or_create_standard_dish(conn, "鱼香肉丝")
            candidate = create_dish_image_candidate(
                conn,
                int(standard_dish["id"]),
                image_url="https://img.example/yuxiang-pending.jpg",
                prompt_version="v2",
            )
        finally:
            conn.close()

        client = self._build_client(self.admin_user)

        response = client.post(
            f"/admin/dish-images/{candidate['id']}/approve",
            json={"note": "Composition is clean enough for release."},
        )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "approved")
        self.assertTrue(payload["isCurrentOfficial"])
        self.assertEqual(payload["recentOperations"][0]["action"], "approve")
        self.assertEqual(payload["recentOperations"][0]["actor"]["email"], "admin@example.com")

        conn = get_db_connection()
        try:
            refreshed_dish = get_standard_dish_by_id(conn, int(candidate["standard_dish_id"]))
        finally:
            conn.close()

        self.assertIsNotNone(refreshed_dish)
        self.assertEqual(refreshed_dish["image_status"], "approved")
        self.assertEqual(refreshed_dish["image_url"], "https://img.example/yuxiang-pending.jpg")

    def test_admin_can_regenerate_approved_candidate_without_clearing_current_official_image(self) -> None:
        conn = get_db_connection()
        try:
            standard_dish = get_or_create_standard_dish(conn, "咖喱鸡饭")
            candidate = create_dish_image_candidate(
                conn,
                int(standard_dish["id"]),
                image_url="https://img.example/curry-approved.jpg",
                prompt_version="v1",
            )
            approve_dish_image_candidate(
                conn,
                int(standard_dish["id"]),
                int(candidate["id"]),
                reviewed_by_user_id=self.admin_user.id,
            )
        finally:
            conn.close()

        client = self._build_client(self.admin_user)

        with patch(
            "backend.services.admin_dish_image_service.dispatch_image_generation_job",
            return_value=True,
        ):
            response = client.post(
                f"/admin/dish-images/{candidate['id']}/regenerate",
                json={"note": "Try a tighter crop."},
            )

        self.assertEqual(response.status_code, 200)
        payload = response.json()
        self.assertEqual(payload["status"], "approved")
        self.assertTrue(payload["isCurrentOfficial"])
        self.assertFalse(payload["canRegenerate"])
        self.assertEqual(payload["recentOperations"][0]["action"], "regenerate")
        self.assertEqual(payload["officialImageUrl"], "https://img.example/curry-approved.jpg")

        conn = get_db_connection()
        try:
            refreshed_dish = get_standard_dish_by_id(conn, int(candidate["standard_dish_id"]))
            active_job = conn.execute(
                """
                SELECT status
                FROM image_generation_jobs
                WHERE standard_dish_id = ?
                ORDER BY id DESC
                LIMIT 1
                """,
                (int(candidate["standard_dish_id"]),),
            ).fetchone()
        finally:
            conn.close()

        self.assertIsNotNone(refreshed_dish)
        self.assertEqual(refreshed_dish["image_url"], "https://img.example/curry-approved.jpg")
        self.assertIsNotNone(active_job)
        self.assertEqual(active_job["status"], "queued")

    def _build_client(self, current_user: UserOut) -> TestClient:
        app = FastAPI()
        app.dependency_overrides[get_current_user] = lambda: current_user
        app.include_router(admin_dish_images_router)
        return TestClient(app)


if __name__ == "__main__":
    unittest.main()
