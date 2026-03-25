import json
import threading
from concurrent.futures import ThreadPoolExecutor
from urllib import error, request

from backend.config.image_generation import (
    StandardDishImageGenerationConfig,
    get_standard_dish_image_generation_config,
)
from backend.database.connection import get_db_connection
from backend.repositories.image_generation_job_repository import (
    IMAGE_GENERATION_JOB_STATUS_COMPLETED,
    IMAGE_GENERATION_JOB_STATUS_FAILED,
    IMAGE_GENERATION_JOB_STATUS_QUEUED,
    IMAGE_GENERATION_JOB_STATUS_RUNNING,
    IMAGE_GENERATION_JOB_STATUS_TIMED_OUT,
    create_image_generation_job,
    get_active_image_generation_job,
    get_image_generation_job_by_id,
    list_image_generation_jobs_by_standard_dish,
    list_image_generation_jobs_by_status,
    mark_image_generation_job_completed,
    mark_image_generation_job_failed,
    mark_image_generation_job_running,
    mark_running_image_generation_jobs_timed_out,
    retry_image_generation_job,
)
from backend.repositories.standard_dish_repository import (
    create_dish_image_candidate,
    get_standard_dish_by_id,
)


_JOB_EXECUTOR = ThreadPoolExecutor(
    max_workers=2,
    thread_name_prefix="standard-dish-image",
)
_DISPATCHED_JOB_IDS: set[int] = set()
_DISPATCH_LOCK = threading.Lock()


def build_standard_dish_image_prompt(
    standard_dish_name: str,
    *,
    config: StandardDishImageGenerationConfig | None = None,
) -> str:
    normalized_name = standard_dish_name.strip()
    if not normalized_name:
        raise ValueError("standard_dish_name is required")
    active_config = config or get_standard_dish_image_generation_config()
    return active_config.prompt_template.format(dish_name=normalized_name)


def enqueue_standard_dish_image_generation(
    standard_dish_id: int,
    *,
    dispatch_async: bool = True,
    config: StandardDishImageGenerationConfig | None = None,
) -> dict[str, object] | None:
    active_config = config or get_standard_dish_image_generation_config()
    conn = get_db_connection()
    try:
        standard_dish = get_standard_dish_by_id(conn, standard_dish_id)
        if standard_dish is None:
            raise LookupError("standard dish not found")

        active_job = get_active_image_generation_job(conn, standard_dish_id)
        if active_job is not None:
            if dispatch_async:
                dispatch_image_generation_job(int(active_job["id"]))
            return active_job

        if not bool(standard_dish["can_trigger_image_generation"]):
            return None

        job = create_image_generation_job(
            conn,
            standard_dish_id,
            prompt_version=active_config.prompt_version,
            prompt_text=build_standard_dish_image_prompt(
                str(standard_dish["canonical_name"]),
                config=active_config,
            ),
        )
    finally:
        conn.close()

    if dispatch_async:
        dispatch_image_generation_job(int(job["id"]))
    return job


def retry_standard_dish_image_generation(
    job_id: int,
    *,
    dispatch_async: bool = True,
) -> dict[str, object]:
    conn = get_db_connection()
    try:
        original_job = get_image_generation_job_by_id(conn, job_id)
        if original_job is None:
            raise LookupError("image generation job not found")

        standard_dish = get_standard_dish_by_id(conn, int(original_job["standard_dish_id"]))
        if standard_dish is None:
            raise LookupError("standard dish not found")
        if not bool(standard_dish["can_trigger_image_generation"]):
            raise ValueError("standard dish is not eligible for image generation retry")

        retried_job = retry_image_generation_job(conn, job_id)
    finally:
        conn.close()

    if dispatch_async:
        dispatch_image_generation_job(int(retried_job["id"]))
    return retried_job


def dispatch_pending_image_generation_jobs(*, limit: int | None = None) -> list[int]:
    conn = get_db_connection()
    try:
        queued_jobs = list_image_generation_jobs_by_status(
            conn,
            IMAGE_GENERATION_JOB_STATUS_QUEUED,
            limit=limit,
        )
    finally:
        conn.close()

    dispatched_job_ids: list[int] = []
    for job in queued_jobs:
        job_id = int(job["id"])
        if dispatch_image_generation_job(job_id):
            dispatched_job_ids.append(job_id)
    return dispatched_job_ids


def recover_and_dispatch_image_generation_jobs() -> dict[str, object]:
    conn = get_db_connection()
    try:
        timed_out_count = mark_running_image_generation_jobs_timed_out(
            conn,
            error_message="worker restarted before image generation completed",
        )
    finally:
        conn.close()

    dispatched_job_ids = dispatch_pending_image_generation_jobs()
    return {
        "timed_out_count": timed_out_count,
        "dispatched_job_ids": dispatched_job_ids,
    }


def process_image_generation_job(
    job_id: int,
    *,
    config: StandardDishImageGenerationConfig | None = None,
) -> dict[str, object]:
    active_config = config or get_standard_dish_image_generation_config()
    conn = get_db_connection()
    try:
        job = mark_image_generation_job_running(conn, job_id)
        if job["status"] == IMAGE_GENERATION_JOB_STATUS_COMPLETED:
            return job
        if job["status"] in {
            IMAGE_GENERATION_JOB_STATUS_FAILED,
            IMAGE_GENERATION_JOB_STATUS_TIMED_OUT,
        }:
            return job

        standard_dish = get_standard_dish_by_id(conn, int(job["standard_dish_id"]))
        if standard_dish is None:
            raise LookupError("standard dish not found")
        if bool(standard_dish["has_official_image"]) or standard_dish.get("image_status") == "pending":
            return mark_image_generation_job_failed(
                conn,
                job_id,
                error_message="standard dish is no longer eligible for image generation result writeback",
            )

        generated_image_url = generate_standard_dish_image_url(
            str(job["prompt_text"]),
            config=active_config,
        )
        candidate = create_dish_image_candidate(
            conn,
            int(job["standard_dish_id"]),
            image_url=generated_image_url,
            prompt_version=str(job["prompt_version"]),
            auto_commit=False,
        )
        completed_job = mark_image_generation_job_completed(
            conn,
            job_id,
            dish_image_id=int(candidate["id"]),
            auto_commit=False,
        )
        conn.commit()
        return completed_job
    except TimeoutError as exc:
        conn.rollback()
        return mark_image_generation_job_failed(
            conn,
            job_id,
            error_message=_stringify_exception(exc),
            status=IMAGE_GENERATION_JOB_STATUS_TIMED_OUT,
        )
    except Exception as exc:
        conn.rollback()
        return mark_image_generation_job_failed(
            conn,
            job_id,
            error_message=_stringify_exception(exc),
            status=IMAGE_GENERATION_JOB_STATUS_FAILED,
        )
    finally:
        conn.close()


def list_standard_dish_image_generation_jobs(
    standard_dish_id: int,
) -> list[dict[str, object]]:
    conn = get_db_connection()
    try:
        return list_image_generation_jobs_by_standard_dish(conn, standard_dish_id)
    finally:
        conn.close()


def generate_standard_dish_image_url(
    prompt: str,
    *,
    config: StandardDishImageGenerationConfig | None = None,
) -> str:
    active_config = config or get_standard_dish_image_generation_config()
    normalized_prompt = prompt.strip()
    if not normalized_prompt:
        raise ValueError("prompt is required")

    if active_config.mock_image_url:
        return active_config.mock_image_url

    if not active_config.enabled:
        raise RuntimeError("standard dish image generation is disabled")
    if not active_config.api_key or not active_config.base_url or not active_config.model:
        raise RuntimeError("standard dish image generation config is incomplete")

    endpoint = f"{active_config.base_url.rstrip('/')}/images/generations"
    payload = {
        "model": active_config.model,
        "prompt": normalized_prompt,
        "size": "1024x1024",
        "response_format": "url",
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {active_config.api_key}",
        },
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=active_config.timeout_seconds) as response:
            data = json.load(response)
    except error.URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, TimeoutError):
            raise TimeoutError("image generation request timed out") from exc
        raise RuntimeError(_stringify_exception(exc)) from exc

    image_url = (
        data.get("data", [{}])[0].get("url")
        if isinstance(data, dict)
        else None
    )
    if not isinstance(image_url, str) or not image_url.strip():
        raise RuntimeError("image generation response did not include a valid image url")
    return image_url.strip()


def dispatch_image_generation_job(job_id: int) -> bool:
    with _DISPATCH_LOCK:
        if job_id in _DISPATCHED_JOB_IDS:
            return False
        _DISPATCHED_JOB_IDS.add(job_id)

    _JOB_EXECUTOR.submit(_process_image_generation_job_in_background, job_id)
    return True


def _process_image_generation_job_in_background(job_id: int) -> None:
    try:
        process_image_generation_job(job_id)
    finally:
        with _DISPATCH_LOCK:
            _DISPATCHED_JOB_IDS.discard(job_id)


def _stringify_exception(exc: Exception) -> str:
    message = str(exc).strip()
    if message:
        return message
    return exc.__class__.__name__
