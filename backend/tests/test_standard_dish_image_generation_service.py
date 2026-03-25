import os
import unittest
from unittest.mock import patch

from backend.config.image_generation import StandardDishImageGenerationConfig
from backend.database.connection import get_db_connection
from backend.database.init_db import init_db
from backend.repositories.standard_dish_repository import (
    get_or_create_standard_dish,
    get_standard_dish_by_id,
    list_dish_images_by_standard_dish,
    list_standard_dishes_ready_for_image_generation,
)
from backend.services.standard_dish_image_generation_service import (
    enqueue_standard_dish_image_generation,
    list_standard_dish_image_generation_jobs,
    process_image_generation_job,
    recover_and_dispatch_image_generation_jobs,
    retry_standard_dish_image_generation,
)


class StandardDishImageGenerationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = os.path.join(
            os.getcwd(),
            "backend",
            "database",
            "test_standard_dish_image_generation_service.db",
        )
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db_patch = patch("backend.database.connection.db_path", self.db_path)
        self.db_patch.start()
        init_db()

    def tearDown(self) -> None:
        self.db_patch.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_init_db_creates_image_generation_jobs_table_and_indexes(self) -> None:
        conn = get_db_connection()
        try:
            table_exists = conn.execute(
                """
                SELECT name
                FROM sqlite_master
                WHERE type = 'table' AND name = 'image_generation_jobs'
                """
            ).fetchone()
            indexes = {
                row["name"]
                for row in conn.execute("PRAGMA index_list(image_generation_jobs)").fetchall()
            }
        finally:
            conn.close()

        self.assertIsNotNone(table_exists)
        self.assertIn("idx_image_generation_jobs_status", indexes)
        self.assertIn("idx_image_generation_jobs_one_active_per_dish", indexes)

    def test_enqueue_is_idempotent_and_removes_dish_from_ready_list_while_job_is_active(self) -> None:
        standard_dish_id = self._create_standard_dish("宫保鸡丁")

        with patch(
            "backend.services.standard_dish_image_generation_service.dispatch_image_generation_job",
            return_value=True,
        ):
            first_job = enqueue_standard_dish_image_generation(standard_dish_id)
            second_job = enqueue_standard_dish_image_generation(standard_dish_id)

        conn = get_db_connection()
        try:
            refreshed_dish = get_standard_dish_by_id(conn, standard_dish_id)
            ready = list_standard_dishes_ready_for_image_generation(conn)
        finally:
            conn.close()

        jobs = list_standard_dish_image_generation_jobs(standard_dish_id)

        self.assertIsNotNone(first_job)
        self.assertEqual(first_job["id"], second_job["id"])
        self.assertEqual(len(jobs), 1)
        self.assertEqual(jobs[0]["status"], "queued")
        self.assertEqual(jobs[0]["prompt_version"], "v1")
        self.assertIn("宫保鸡丁", str(jobs[0]["prompt_text"]))
        self.assertTrue(bool(refreshed_dish["has_active_image_generation_job"]))
        self.assertFalse(bool(refreshed_dish["can_trigger_image_generation"]))
        self.assertEqual(ready, [])

    def test_process_completed_job_creates_pending_candidate_and_preserves_non_blocking_status(self) -> None:
        standard_dish_id = self._create_standard_dish("番茄炒蛋")
        config = _build_test_config("https://img.example/tomato-egg-generated.jpg")

        job = enqueue_standard_dish_image_generation(
            standard_dish_id,
            dispatch_async=False,
            config=config,
        )
        completed_job = process_image_generation_job(
            int(job["id"]),
            config=config,
        )

        conn = get_db_connection()
        try:
            refreshed_dish = get_standard_dish_by_id(conn, standard_dish_id)
            images = list_dish_images_by_standard_dish(conn, standard_dish_id)
        finally:
            conn.close()

        self.assertEqual(completed_job["status"], "completed")
        self.assertIsNotNone(completed_job["dish_image_id"])
        self.assertEqual(len(images), 1)
        self.assertEqual(images[0]["status"], "pending")
        self.assertEqual(images[0]["image_url"], "https://img.example/tomato-egg-generated.jpg")
        self.assertEqual(images[0]["prompt_version"], "v1")
        self.assertEqual(refreshed_dish["image_status"], "pending")
        self.assertIsNone(refreshed_dish["image_url"])
        self.assertFalse(bool(refreshed_dish["can_trigger_image_generation"]))

    def test_failed_job_is_auditable_and_can_be_retried(self) -> None:
        standard_dish_id = self._create_standard_dish("红烧牛肉面")
        failed_job = enqueue_standard_dish_image_generation(
            standard_dish_id,
            dispatch_async=False,
        )

        with patch(
            "backend.services.standard_dish_image_generation_service.generate_standard_dish_image_url",
            side_effect=RuntimeError("upstream image provider failed"),
        ):
            failed_result = process_image_generation_job(int(failed_job["id"]))

        conn = get_db_connection()
        try:
            refreshed_after_failure = get_standard_dish_by_id(conn, standard_dish_id)
            images_after_failure = list_dish_images_by_standard_dish(conn, standard_dish_id)
        finally:
            conn.close()

        self.assertEqual(failed_result["status"], "failed")
        self.assertEqual(failed_result["error_message"], "upstream image provider failed")
        self.assertEqual(images_after_failure, [])
        self.assertTrue(bool(refreshed_after_failure["can_trigger_image_generation"]))

        retry_config = _build_test_config("https://img.example/beef-noodle-retry.jpg")
        retried_job = retry_standard_dish_image_generation(
            int(failed_job["id"]),
            dispatch_async=False,
        )
        retried_result = process_image_generation_job(
            int(retried_job["id"]),
            config=retry_config,
        )

        conn = get_db_connection()
        try:
            images_after_retry = list_dish_images_by_standard_dish(conn, standard_dish_id)
        finally:
            conn.close()

        jobs = list_standard_dish_image_generation_jobs(standard_dish_id)

        self.assertNotEqual(retried_job["id"], failed_job["id"])
        self.assertEqual(retried_job["retry_of_job_id"], failed_job["id"])
        self.assertEqual(retried_result["status"], "completed")
        self.assertEqual(len(jobs), 2)
        self.assertEqual(images_after_retry[0]["image_url"], "https://img.example/beef-noodle-retry.jpg")

    def test_timeout_job_is_marked_timed_out_without_creating_candidate(self) -> None:
        standard_dish_id = self._create_standard_dish("鱼香肉丝")
        job = enqueue_standard_dish_image_generation(
            standard_dish_id,
            dispatch_async=False,
        )

        with patch(
            "backend.services.standard_dish_image_generation_service.generate_standard_dish_image_url",
            side_effect=TimeoutError("provider timeout"),
        ):
            timed_out_job = process_image_generation_job(int(job["id"]))

        conn = get_db_connection()
        try:
            refreshed_dish = get_standard_dish_by_id(conn, standard_dish_id)
            images = list_dish_images_by_standard_dish(conn, standard_dish_id)
        finally:
            conn.close()

        self.assertEqual(timed_out_job["status"], "timed_out")
        self.assertEqual(timed_out_job["error_message"], "provider timeout")
        self.assertEqual(images, [])
        self.assertTrue(bool(refreshed_dish["can_trigger_image_generation"]))

    def test_recover_marks_running_jobs_timed_out_and_dispatches_queued_jobs(self) -> None:
        config = _build_test_config("https://img.example/recover.jpg")
        queued_dish_id = self._create_standard_dish("青椒土豆丝")
        running_dish_id = self._create_standard_dish("麻婆豆腐")
        queued_job = enqueue_standard_dish_image_generation(
            queued_dish_id,
            dispatch_async=False,
            config=config,
        )
        running_job = enqueue_standard_dish_image_generation(
            running_dish_id,
            dispatch_async=False,
            config=config,
        )
        process_image_generation_job(int(running_job["id"]), config=config)

        conn = get_db_connection()
        try:
            conn.execute(
                """
                UPDATE image_generation_jobs
                SET
                    status = 'running',
                    started_at = CURRENT_TIMESTAMP,
                    finished_at = NULL,
                    dish_image_id = NULL
                WHERE id = ?
                """,
                (running_job["id"],),
            )
            conn.execute(
                """
                DELETE FROM dish_images
                WHERE standard_dish_id = ?
                """,
                (running_dish_id,),
            )
            conn.execute(
                """
                UPDATE standard_dishes
                SET
                    image_status = NULL,
                    image_url = NULL,
                    image_prompt_version = NULL,
                    image_updated_at = NULL
                WHERE id = ?
                """,
                (running_dish_id,),
            )
            conn.commit()
        finally:
            conn.close()

        with patch(
            "backend.services.standard_dish_image_generation_service.dispatch_image_generation_job",
            return_value=True,
        ):
            recovery = recover_and_dispatch_image_generation_jobs()

        jobs = list_standard_dish_image_generation_jobs(running_dish_id)

        self.assertEqual(recovery["timed_out_count"], 1)
        self.assertEqual(recovery["dispatched_job_ids"], [queued_job["id"]])
        self.assertEqual(jobs[0]["status"], "timed_out")
        self.assertEqual(
            jobs[0]["error_message"],
            "worker restarted before image generation completed",
        )

    def _create_standard_dish(self, name: str) -> int:
        conn = get_db_connection()
        try:
            standard_dish = get_or_create_standard_dish(conn, name)
            return int(standard_dish["id"])
        finally:
            conn.close()


def _build_test_config(mock_image_url: str) -> StandardDishImageGenerationConfig:
    return StandardDishImageGenerationConfig(
        enabled=True,
        api_key="",
        base_url="",
        model="mock-model",
        timeout_seconds=5,
        prompt_version="v1",
        prompt_template='Generate a cover image for "{dish_name}".',
        mock_image_url=mock_image_url,
    )


if __name__ == "__main__":
    unittest.main()
