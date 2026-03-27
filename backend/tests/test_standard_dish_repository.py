import os
import unittest
from unittest.mock import patch

from backend.database.connection import get_db_connection
from backend.database.init_db import init_db
from backend.repositories.food_log_repository import create_food_log
from backend.repositories.standard_dish_repository import (
    approve_dish_image_candidate,
    can_trigger_standard_dish_image_generation,
    create_dish_image_candidate,
    get_or_create_standard_dish,
    get_standard_dish_by_id,
    list_dish_images_by_standard_dish,
    list_standard_dishes_ready_for_image_generation,
    reject_dish_image_candidate,
)


class StandardDishRepositoryTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = os.path.join(
            os.getcwd(),
            "backend",
            "database",
            "test_standard_dish_repository.db",
        )
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db_patch = patch("backend.database.connection.db_path", self.db_path)
        self.db_patch.start()
        init_db()

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (email, password_hash, display_name)
                VALUES (?, ?, ?)
                """,
                ("owner@example.com", "hashed-password", "Owner"),
            )
            self.user_id = cursor.lastrowid
            cursor.execute(
                """
                INSERT INTO chat_sessions (user_id, title)
                VALUES (?, ?)
                """,
                (self.user_id, "Session A"),
            )
            self.session_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()

    def tearDown(self) -> None:
        self.db_patch.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_init_db_creates_standard_dish_tables_and_indexes(self) -> None:
        conn = get_db_connection()
        try:
            standard_dish_indexes = {
                row["name"]
                for row in conn.execute("PRAGMA index_list(standard_dishes)").fetchall()
            }
            dish_image_indexes = {
                row["name"]
                for row in conn.execute("PRAGMA index_list(dish_images)").fetchall()
            }
            foreign_keys = conn.execute("PRAGMA foreign_key_list(dish_images)").fetchall()
        finally:
            conn.close()

        self.assertIn("idx_standard_dishes_normalized_name_unique", standard_dish_indexes)
        self.assertIn("idx_standard_dishes_image_status", standard_dish_indexes)
        self.assertIn("idx_dish_images_one_pending_per_dish", dish_image_indexes)
        self.assertIn("idx_dish_images_one_approved_per_dish", dish_image_indexes)
        self.assertEqual({row["table"] for row in foreign_keys}, {"standard_dishes", "users"})

    def test_get_or_create_standard_dish_normalizes_duplicate_names(self) -> None:
        conn = get_db_connection()
        try:
            first = get_or_create_standard_dish(conn, " 宫保鸡丁 ")
            second = get_or_create_standard_dish(conn, "宫保鸡丁")
        finally:
            conn.close()

        self.assertEqual(first["id"], second["id"])
        self.assertEqual(first["normalized_name"], "宫保鸡丁")

    def test_standard_dish_without_official_image_is_generation_ready(self) -> None:
        conn = get_db_connection()
        try:
            standard_dish = get_or_create_standard_dish(conn, "番茄炒蛋")
            ready = list_standard_dishes_ready_for_image_generation(conn)
            can_trigger = can_trigger_standard_dish_image_generation(conn, int(standard_dish["id"]))
        finally:
            conn.close()

        self.assertTrue(standard_dish["can_trigger_image_generation"])
        self.assertFalse(standard_dish["has_official_image"])
        self.assertTrue(can_trigger)
        self.assertEqual([entry["id"] for entry in ready], [standard_dish["id"]])

    def test_creating_pending_candidate_marks_dish_pending(self) -> None:
        conn = get_db_connection()
        try:
            standard_dish = get_or_create_standard_dish(conn, "红烧牛肉面")
            candidate = create_dish_image_candidate(
                conn,
                int(standard_dish["id"]),
                image_url="https://img.example/beef-noodle-pending.jpg",
                prompt_version="v1",
            )
            refreshed = get_standard_dish_by_id(conn, int(standard_dish["id"]))
            ready = list_standard_dishes_ready_for_image_generation(conn)
        finally:
            conn.close()

        self.assertEqual(candidate["status"], "pending")
        self.assertEqual(candidate["prompt_version"], "v1")
        self.assertEqual(refreshed["image_status"], "pending")
        self.assertIsNone(refreshed["image_url"])
        self.assertFalse(refreshed["can_trigger_image_generation"])
        self.assertEqual(ready, [])

    def test_approve_candidate_sets_unique_official_image(self) -> None:
        conn = get_db_connection()
        try:
            standard_dish = get_or_create_standard_dish(conn, "牛肉炒饭")
            first_candidate = create_dish_image_candidate(
                conn,
                int(standard_dish["id"]),
                image_url="https://img.example/fried-rice-approved.jpg",
                prompt_version="v1",
            )
            approved = approve_dish_image_candidate(
                conn,
                int(standard_dish["id"]),
                int(first_candidate["id"]),
            )
            second_candidate = create_dish_image_candidate(
                conn,
                int(standard_dish["id"]),
                image_url="https://img.example/fried-rice-alt.jpg",
                prompt_version="v2",
            )
            replaced = approve_dish_image_candidate(
                conn,
                int(standard_dish["id"]),
                int(second_candidate["id"]),
            )
            images = list_dish_images_by_standard_dish(conn, int(standard_dish["id"]))
        finally:
            conn.close()

        self.assertEqual(approved["image_status"], "approved")
        self.assertEqual(approved["image_url"], "https://img.example/fried-rice-approved.jpg")
        self.assertEqual(approved["image_prompt_version"], "v1")
        self.assertTrue(approved["has_official_image"])
        self.assertFalse(approved["can_trigger_image_generation"])
        self.assertEqual(replaced["image_url"], "https://img.example/fried-rice-alt.jpg")
        self.assertEqual(replaced["image_prompt_version"], "v2")
        self.assertEqual(images[0]["status"], "approved")
        self.assertEqual(images[1]["status"], "rejected")

    def test_reject_candidate_restores_generation_ready_state_without_official_image(self) -> None:
        conn = get_db_connection()
        try:
            standard_dish = get_or_create_standard_dish(conn, "鱼香肉丝")
            candidate = create_dish_image_candidate(
                conn,
                int(standard_dish["id"]),
                image_url="https://img.example/yuxiang.jpg",
                prompt_version="v3",
            )
            rejected = reject_dish_image_candidate(
                conn,
                int(standard_dish["id"]),
                int(candidate["id"]),
                review_note="构图不稳定",
            )
            images = list_dish_images_by_standard_dish(conn, int(standard_dish["id"]))
        finally:
            conn.close()

        self.assertEqual(rejected["image_status"], "rejected")
        self.assertIsNone(rejected["image_url"])
        self.assertTrue(rejected["can_trigger_image_generation"])
        self.assertEqual(images[0]["status"], "rejected")
        self.assertEqual(images[0]["review_note"], "构图不稳定")

    def test_rejecting_non_official_candidate_preserves_existing_official_image(self) -> None:
        conn = get_db_connection()
        try:
            standard_dish = get_or_create_standard_dish(conn, "咖喱鸡饭")
            approved_candidate = create_dish_image_candidate(
                conn,
                int(standard_dish["id"]),
                image_url="https://img.example/curry-approved.jpg",
                prompt_version="v1",
            )
            approve_dish_image_candidate(
                conn,
                int(standard_dish["id"]),
                int(approved_candidate["id"]),
            )
            pending_candidate = create_dish_image_candidate(
                conn,
                int(standard_dish["id"]),
                image_url="https://img.example/curry-regenerate.jpg",
                prompt_version="v2",
            )
            rejected = reject_dish_image_candidate(
                conn,
                int(standard_dish["id"]),
                int(pending_candidate["id"]),
                review_note="背景不统一",
            )
        finally:
            conn.close()

        self.assertEqual(rejected["image_status"], "approved")
        self.assertEqual(rejected["image_url"], "https://img.example/curry-approved.jpg")
        self.assertEqual(rejected["image_prompt_version"], "v1")
        self.assertFalse(rejected["can_trigger_image_generation"])

    def test_rejected_candidate_does_not_affect_food_log_save(self) -> None:
        conn = get_db_connection()
        try:
            standard_dish = get_or_create_standard_dish(conn, "鸡胸肉沙拉")
            candidate = create_dish_image_candidate(
                conn,
                int(standard_dish["id"]),
                image_url="https://img.example/salad.jpg",
                prompt_version="v1",
            )
            reject_dish_image_candidate(
                conn,
                int(standard_dish["id"]),
                int(candidate["id"]),
                review_note="成图质量不足",
            )
            food_log = create_food_log(
                conn,
                self.user_id,
                source_type="manual",
                session_id=self.session_id,
                meal_description="鸡胸肉沙拉",
                result_title="鸡胸肉沙拉",
                result_description="手动记录不应受图片审核状态影响。",
                total_calories="320 kcal",
                ingredients=[],
                is_manual=True,
            )
        finally:
            conn.close()

        self.assertEqual(food_log["result_title"], "鸡胸肉沙拉")
        self.assertEqual(food_log["status"], "active")


if __name__ == "__main__":
    unittest.main()
