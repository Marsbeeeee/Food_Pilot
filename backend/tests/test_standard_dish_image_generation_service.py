import http.client
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
    build_standard_dish_image_prompt,
    enqueue_standard_dish_image_generation,
    generate_standard_dish_image_url,
    list_standard_dish_image_generation_jobs,
    persist_standard_dish_image_asset,
    process_image_generation_job,
    recover_and_dispatch_image_generation_jobs,
    retry_standard_dish_image_generation,
)


class StandardDishImageGenerationServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.asset_dir = os.path.join(os.getcwd(), "backend", "generated_assets_test")
        self.db_path = os.path.join(
            os.getcwd(),
            "backend",
            "database",
            "test_standard_dish_image_generation_service.db",
        )
        if os.path.isdir(self.asset_dir):
            for name in os.listdir(self.asset_dir):
                os.remove(os.path.join(self.asset_dir, name))
        else:
            os.makedirs(self.asset_dir, exist_ok=True)
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db_patch = patch("backend.database.connection.db_path", self.db_path)
        self.db_patch.start()
        init_db()

    def tearDown(self) -> None:
        self.db_patch.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        if os.path.isdir(self.asset_dir):
            for name in os.listdir(self.asset_dir):
                os.remove(os.path.join(self.asset_dir, name))
            os.rmdir(self.asset_dir)

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
        standard_dish_id = self._create_standard_dish("kung pao chicken")

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
        self.assertEqual(jobs[0]["prompt_version"], "v2")
        self.assertIn("kung pao chicken", str(jobs[0]["prompt_text"]))
        self.assertIn("Dish-specific details for this dish:", str(jobs[0]["prompt_text"]))
        self.assertIn("Dish category:", str(jobs[0]["prompt_text"]))
        self.assertTrue(bool(refreshed_dish["has_active_image_generation_job"]))
        self.assertFalse(bool(refreshed_dish["can_trigger_image_generation"]))
        self.assertEqual(ready, [])

    def test_build_prompt_auto_expands_for_high_frequency_dish_types(self) -> None:
        config = _build_test_config()

        stir_fried_noodle_prompt = build_standard_dish_image_prompt(
            "beef fried noodle",
            config=config,
        )
        pizza_prompt = build_standard_dish_image_prompt(
            "Margherita Pizza",
            config=config,
        )

        self.assertIn("Dish category: stir_fried_noodle", stir_fried_noodle_prompt)
        self.assertIn("plate-style stir-fried noodles", stir_fried_noodle_prompt)
        self.assertIn("Dish category: pizza", pizza_prompt)
        self.assertIn("round thin-crust pizza", pizza_prompt)

    def test_build_prompt_falls_back_to_generic_food_when_dish_type_is_ambiguous(self) -> None:
        config = _build_test_config()

        prompt = build_standard_dish_image_prompt(
            "mystery energy bowl",
            config=config,
        )
        steak_prompt = build_standard_dish_image_prompt(
            "beef steak",
            config=config,
        )

        self.assertIn("Dish category: generic_food", prompt)
        self.assertIn("Use a clean bowl or plate with minimal props", prompt)
        self.assertIn("Dish category: generic_food", steak_prompt)

    def test_process_completed_job_creates_pending_candidate_and_preserves_non_blocking_status(self) -> None:
        standard_dish_id = self._create_standard_dish("tomato egg")
        config = _build_test_config()

        job = enqueue_standard_dish_image_generation(
            standard_dish_id,
            dispatch_async=False,
            config=config,
        )
        with patch(
            "backend.services.standard_dish_image_generation_service.generate_standard_dish_image_url",
            return_value="https://img.example/tomato-egg-generated.jpg",
        ), patch(
            "backend.services.standard_dish_image_generation_service.persist_standard_dish_image_asset",
            return_value="https://img.example/tomato-egg-generated.jpg",
        ):
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
        standard_dish_id = self._create_standard_dish("braised beef noodle")
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

        retry_config = _build_test_config()
        retried_job = retry_standard_dish_image_generation(
            int(failed_job["id"]),
            dispatch_async=False,
        )
        with patch(
            "backend.services.standard_dish_image_generation_service.generate_standard_dish_image_url",
            return_value="https://img.example/beef-noodle-retry.jpg",
        ), patch(
            "backend.services.standard_dish_image_generation_service.persist_standard_dish_image_asset",
            return_value="https://img.example/beef-noodle-retry.jpg",
        ):
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
        standard_dish_id = self._create_standard_dish("fish with chili sauce")
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
        config = _build_test_config()
        queued_dish_id = self._create_standard_dish("stir-fried potato strips")
        running_dish_id = self._create_standard_dish("mapo tofu")
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
        with patch(
            "backend.services.standard_dish_image_generation_service.generate_standard_dish_image_url",
            return_value="https://img.example/recover.jpg",
        ), patch(
            "backend.services.standard_dish_image_generation_service.persist_standard_dish_image_asset",
            return_value="https://img.example/recover.jpg",
        ):
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

    def test_generate_uses_dashscope_sync_api_for_qwen_image_2_models(self) -> None:
        config = StandardDishImageGenerationConfig(
            enabled=True,
            api_key="test-key",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-image-2.0-pro",
            timeout_seconds=5,
            prompt_version="v1",
            prompt_template='Generate a cover image for "{dish_name}".',
            public_base_url="http://localhost:8000",
            storage_dir=os.path.join(os.getcwd(), "backend", "generated_assets_test"),
        )
        with patch(
            "backend.services.standard_dish_image_generation_service.request.urlopen",
            return_value=_FakeJsonResponse(
                {
                    "output": {
                        "choices": [
                            {
                                "message": {
                                    "content": [
                                        {
                                            "image": "https://img.example/dashscope-generated.png",
                                        }
                                    ]
                                }
                            }
                        ]
                    }
                }
            ),
        ) as mock_urlopen:
            image_url = generate_standard_dish_image_url(
                "margherita pizza",
                config=config,
            )

        self.assertEqual(image_url, "https://img.example/dashscope-generated.png")
        self.assertEqual(mock_urlopen.call_count, 1)
        submit_request = mock_urlopen.call_args_list[0].args[0]
        self.assertEqual(
            submit_request.full_url,
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation",
        )
        self.assertEqual(submit_request.get_method(), "POST")
        self.assertNotIn("X-dashscope-async", submit_request.headers)

    def test_generate_uses_dashscope_async_api_for_legacy_qwen_image_models(self) -> None:
        config = StandardDishImageGenerationConfig(
            enabled=True,
            api_key="test-key",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-image-plus",
            timeout_seconds=5,
            prompt_version="v1",
            prompt_template='Generate a cover image for "{dish_name}".',
            public_base_url="http://localhost:8000",
            storage_dir=os.path.join(os.getcwd(), "backend", "generated_assets_test"),
        )
        responses = [
            _FakeJsonResponse(
                {
                    "output": {
                        "task_id": "task-789",
                        "task_status": "PENDING",
                    }
                }
            ),
            _FakeJsonResponse(
                {
                    "output": {
                        "task_id": "task-789",
                        "task_status": "RUNNING",
                    }
                }
            ),
            _FakeJsonResponse(
                {
                    "output": {
                        "task_id": "task-789",
                        "task_status": "SUCCEEDED",
                        "results": [
                            {
                                "url": "https://img.example/dashscope-legacy-generated.png",
                            }
                        ],
                    }
                }
            ),
        ]

        with patch(
            "backend.services.standard_dish_image_generation_service.request.urlopen",
            side_effect=responses,
        ) as mock_urlopen, patch(
            "backend.services.standard_dish_image_generation_service.time.sleep",
            return_value=None,
        ):
            image_url = generate_standard_dish_image_url(
                "margherita pizza",
                config=config,
            )

        self.assertEqual(image_url, "https://img.example/dashscope-legacy-generated.png")
        self.assertEqual(mock_urlopen.call_count, 3)
        submit_request = mock_urlopen.call_args_list[0].args[0]
        poll_request = mock_urlopen.call_args_list[1].args[0]
        self.assertEqual(
            submit_request.full_url,
            "https://dashscope.aliyuncs.com/api/v1/services/aigc/text2image/image-synthesis",
        )
        self.assertEqual(submit_request.get_method(), "POST")
        self.assertEqual(submit_request.headers["X-dashscope-async"], "enable")
        self.assertEqual(
            poll_request.full_url,
            "https://dashscope.aliyuncs.com/api/v1/tasks/task-789",
        )
        self.assertEqual(poll_request.get_method(), "GET")

    def test_generate_raises_meaningful_error_when_dashscope_task_fails(self) -> None:
        config = StandardDishImageGenerationConfig(
            enabled=True,
            api_key="test-key",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-image-plus",
            timeout_seconds=5,
            prompt_version="v1",
            prompt_template='Generate a cover image for "{dish_name}".',
            public_base_url="http://localhost:8000",
            storage_dir=os.path.join(os.getcwd(), "backend", "generated_assets_test"),
        )
        responses = [
            _FakeJsonResponse(
                {
                    "output": {
                        "task_id": "task-456",
                        "task_status": "PENDING",
                    }
                }
            ),
            _FakeJsonResponse(
                {
                    "output": {
                        "task_id": "task-456",
                        "task_status": "FAILED",
                        "code": "InvalidParameter",
                        "message": "bad prompt",
                    }
                }
            ),
        ]

        with patch(
            "backend.services.standard_dish_image_generation_service.request.urlopen",
            side_effect=responses,
        ), patch(
            "backend.services.standard_dish_image_generation_service.time.sleep",
            return_value=None,
        ):
            with self.assertRaises(RuntimeError) as context:
                generate_standard_dish_image_url(
                    "margherita pizza",
                    config=config,
                )

        self.assertEqual(str(context.exception), "InvalidParameter bad prompt")

    def test_persist_generated_image_asset_stores_local_copy_and_returns_stable_url(self) -> None:
        config = _build_test_config()

        with patch(
            "backend.services.standard_dish_image_generation_service.request.urlopen",
            return_value=_FakeBinaryResponse(
                b"fake-image-bytes",
                content_type="image/png",
            ),
        ):
            persisted_url = persist_standard_dish_image_asset(
                "https://dashscope.aliyuncs.com/generated/temp.png?Expires=123",
                standard_dish_id=12,
                config=config,
            )

        self.assertTrue(
            persisted_url.startswith(
                "http://localhost:8000/generated-assets/standard-dish-images/dish-12-"
            )
        )
        stored_files = os.listdir(self.asset_dir)
        self.assertEqual(len(stored_files), 1)
        self.assertTrue(stored_files[0].endswith(".png"))
        with open(os.path.join(self.asset_dir, stored_files[0]), "rb") as stored_file:
            self.assertEqual(stored_file.read(), b"fake-image-bytes")

    def test_persist_generated_image_asset_accepts_incomplete_read_partial_bytes(self) -> None:
        config = _build_test_config()

        with patch(
            "backend.services.standard_dish_image_generation_service.request.urlopen",
            return_value=_FakeBinaryResponse(
                b"fake-image-bytes",
                content_type="image/png",
                raise_incomplete_read=True,
            ),
        ):
            persisted_url = persist_standard_dish_image_asset(
                "https://dashscope.aliyuncs.com/generated/temp.png?Expires=123",
                standard_dish_id=13,
                config=config,
            )

        self.assertIn("/dish-13-", persisted_url)
        stored_files = os.listdir(self.asset_dir)
        self.assertEqual(len(stored_files), 1)
        with open(os.path.join(self.asset_dir, stored_files[0]), "rb") as stored_file:
            self.assertEqual(stored_file.read(), b"fake-image-bytes")

    def _create_standard_dish(self, name: str) -> int:
        conn = get_db_connection()
        try:
            standard_dish = get_or_create_standard_dish(conn, name)
            return int(standard_dish["id"])
        finally:
            conn.close()


def _build_test_config() -> StandardDishImageGenerationConfig:
    return StandardDishImageGenerationConfig(
        enabled=True,
        api_key="test-key",
        base_url="https://api.example.com/v1",
        model="test-image-model",
        timeout_seconds=5,
        prompt_version="v1",
        prompt_template='Generate a cover image for "{dish_name}".',
        public_base_url="http://localhost:8000",
        storage_dir=os.path.join(os.getcwd(), "backend", "generated_assets_test"),
    )


if __name__ == "__main__":
    unittest.main()


class _FakeJsonResponse:
    def __init__(self, payload: dict[str, object]) -> None:
        self._payload = payload

    def read(self, *_args: object, **_kwargs: object) -> bytes:
        import json

        return json.dumps(self._payload).encode("utf-8")

    def __enter__(self) -> "_FakeJsonResponse":
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> bool:
        return False


class _FakeBinaryResponse:
    def __init__(
        self,
        payload: bytes,
        *,
        content_type: str,
        raise_incomplete_read: bool = False,
    ) -> None:
        self._payload = payload
        self.headers = {"Content-Type": content_type}
        self._raise_incomplete_read = raise_incomplete_read

    def read(self, *_args: object, **_kwargs: object) -> bytes:
        if self._raise_incomplete_read:
            raise http.client.IncompleteRead(self._payload, 10)
        return self._payload

    def __enter__(self) -> "_FakeBinaryResponse":
        return self

    def __exit__(self, exc_type, exc, exc_tb) -> bool:
        return False
