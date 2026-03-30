import http.client
import json
import mimetypes
import sqlite3
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from urllib import error, request
from urllib.parse import urlparse
from uuid import uuid4

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
    get_pending_dish_image,
    reject_dish_image_candidate,
)
from backend.services.standard_dish_image_prompt_builder import (
    build_standard_dish_prompt_expansion_section,
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
    base_prompt = active_config.prompt_template.format(dish_name=normalized_name).strip()
    prompt_expansion = build_standard_dish_prompt_expansion_section(normalized_name)
    return f"{base_prompt}\n\n{prompt_expansion}".strip()


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


def enqueue_admin_standard_dish_image_regeneration(
    standard_dish_id: int,
    *,
    conn: sqlite3.Connection | None = None,
    replace_pending: bool = False,
    reviewed_by_user_id: int | None = None,
    review_note: str | None = None,
    dispatch_async: bool = True,
    config: StandardDishImageGenerationConfig | None = None,
) -> dict[str, object]:
    active_config = config or get_standard_dish_image_generation_config()
    owns_connection = conn is None
    active_conn = conn or get_db_connection()
    try:
        standard_dish = get_standard_dish_by_id(active_conn, standard_dish_id)
        if standard_dish is None:
            raise LookupError("standard dish not found")

        pending_image = get_pending_dish_image(active_conn, standard_dish_id)
        if pending_image is not None:
            if not replace_pending:
                raise ValueError("standard dish already has a pending image candidate")
            reject_dish_image_candidate(
                active_conn,
                standard_dish_id,
                int(pending_image["id"]),
                reviewed_by_user_id=reviewed_by_user_id,
                review_note=review_note or "Rejected before regenerate",
                auto_commit=False,
            )
            cleanup_local_standard_dish_image_asset_if_unreferenced(
                str(pending_image["image_url"]),
                conn=active_conn,
                config=active_config,
            )

        active_job = get_active_image_generation_job(active_conn, standard_dish_id)
        if active_job is not None:
            if dispatch_async:
                dispatch_image_generation_job(int(active_job["id"]))
            if pending_image is not None and owns_connection:
                active_conn.commit()
            return active_job

        job = create_image_generation_job(
            active_conn,
            standard_dish_id,
            prompt_version=active_config.prompt_version,
            prompt_text=build_standard_dish_image_prompt(
                str(standard_dish["canonical_name"]),
                config=active_config,
            ),
            auto_commit=False,
        )
        if owns_connection:
            active_conn.commit()
    finally:
        if owns_connection:
            active_conn.close()

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
        persisted_image_url = persist_standard_dish_image_asset(
            generated_image_url,
            standard_dish_id=int(job["standard_dish_id"]),
            config=active_config,
        )
        candidate = create_dish_image_candidate(
            conn,
            int(job["standard_dish_id"]),
            image_url=persisted_image_url,
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

    if not active_config.enabled:
        raise RuntimeError("standard dish image generation is disabled")
    if not active_config.api_key or not active_config.base_url or not active_config.model:
        raise RuntimeError("standard dish image generation config is incomplete")

    if _should_use_dashscope_native_image_api(active_config):
        return _generate_dashscope_image_url(
            normalized_prompt,
            config=active_config,
        )

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


def _should_use_dashscope_native_image_api(
    config: StandardDishImageGenerationConfig,
) -> bool:
    normalized_model = config.model.strip().lower()
    if not normalized_model.startswith("qwen-image"):
        return False

    parsed = urlparse(config.base_url.strip())
    host = parsed.netloc.lower()
    return "dashscope.aliyuncs.com" in host


def persist_standard_dish_image_asset(
    source_image_url: str,
    *,
    standard_dish_id: int,
    config: StandardDishImageGenerationConfig | None = None,
) -> str:
    active_config = config or get_standard_dish_image_generation_config()
    normalized_source_url = source_image_url.strip()
    if not normalized_source_url:
        raise ValueError("source_image_url is required")

    storage_dir = Path(active_config.storage_dir)
    storage_dir.mkdir(parents=True, exist_ok=True)

    req = request.Request(
        normalized_source_url,
        headers={
            "User-Agent": "FoodPilot/1.0",
        },
        method="GET",
    )
    try:
        with request.urlopen(req, timeout=active_config.timeout_seconds) as response:
            try:
                image_bytes = response.read()
            except http.client.IncompleteRead as exc:
                image_bytes = exc.partial
            content_type = response.headers.get("Content-Type", "")
    except error.HTTPError as exc:
        raise RuntimeError(_extract_http_error_detail(exc)) from exc
    except error.URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, TimeoutError):
            raise TimeoutError("generated image download timed out") from exc
        raise RuntimeError(_stringify_exception(exc)) from exc

    if not image_bytes:
        raise RuntimeError("generated image download returned empty content")

    file_extension = _resolve_image_file_extension(
        content_type=content_type,
        source_url=normalized_source_url,
    )
    file_name = f"dish-{standard_dish_id}-{uuid4().hex}{file_extension}"
    file_path = storage_dir / file_name
    file_path.write_bytes(image_bytes)

    public_base_url = active_config.public_base_url.rstrip("/")
    return f"{public_base_url}/generated-assets/standard-dish-images/{file_name}"


def cleanup_local_standard_dish_image_asset_if_unreferenced(
    image_url: str,
    *,
    conn: sqlite3.Connection | None = None,
    config: StandardDishImageGenerationConfig | None = None,
) -> bool:
    normalized_url = image_url.strip()
    if not normalized_url:
        return False

    file_name = _extract_local_generated_asset_filename(normalized_url)
    if file_name is None:
        return False

    active_config = config or get_standard_dish_image_generation_config()
    owns_conn = conn is None
    active_conn = conn or get_db_connection()
    try:
        referenced_by_active_candidates = int(
            active_conn.execute(
                """
                SELECT COUNT(*) AS total
                FROM dish_images
                WHERE image_url = ?
                  AND status IN ('pending', 'approved')
                """,
                (normalized_url,),
            ).fetchone()["total"]
        )
        referenced_by_official = int(
            active_conn.execute(
                """
                SELECT COUNT(*) AS total
                FROM standard_dishes
                WHERE image_url = ?
                """,
                (normalized_url,),
            ).fetchone()["total"]
        )
    finally:
        if owns_conn:
            active_conn.close()

    if referenced_by_active_candidates > 0 or referenced_by_official > 0:
        return False

    storage_dir = Path(active_config.storage_dir).resolve()
    target_path = (storage_dir / file_name).resolve()
    if target_path.parent != storage_dir:
        return False
    if not target_path.exists():
        return False

    target_path.unlink()
    return True


def _generate_dashscope_image_url(
    prompt: str,
    *,
    config: StandardDishImageGenerationConfig,
) -> str:
    if _should_use_dashscope_multimodal_sync_api(config.model):
        return _generate_dashscope_sync_image_url(
            prompt,
            config=config,
        )

    endpoint = (
        f"{_get_dashscope_api_origin(config.base_url)}"
        "/api/v1/services/aigc/text2image/image-synthesis"
    )
    payload = {
        "model": config.model,
        "input": {
            "prompt": prompt,
        },
        "parameters": {
            "size": _resolve_dashscope_image_size(config.model),
            "n": 1,
            "prompt_extend": True,
            "watermark": False,
        },
    }
    task_response = _open_json_request(
        endpoint,
        payload=payload,
        headers={
            "Authorization": f"Bearer {config.api_key}",
            "X-DashScope-Async": "enable",
        },
        timeout_seconds=config.timeout_seconds,
    )
    task_id = (
        task_response.get("output", {}).get("task_id")
        if isinstance(task_response, dict)
        else None
    )
    if not isinstance(task_id, str) or not task_id.strip():
        raise RuntimeError("dashscope image generation response did not include a task id")

    return _poll_dashscope_image_task(
        task_id.strip(),
        config=config,
    )


def _generate_dashscope_sync_image_url(
    prompt: str,
    *,
    config: StandardDishImageGenerationConfig,
) -> str:
    endpoint = (
        f"{_get_dashscope_api_origin(config.base_url)}"
        "/api/v1/services/aigc/multimodal-generation/generation"
    )
    payload = {
        "model": config.model,
        "input": {
            "messages": [
                {
                    "role": "user",
                    "content": [
                        {
                            "text": prompt,
                        }
                    ],
                }
            ]
        },
        "parameters": {
            "prompt_extend": True,
            "watermark": False,
            "size": _resolve_dashscope_image_size(config.model),
        },
    }
    response_payload = _open_json_request(
        endpoint,
        payload=payload,
        headers={
            "Authorization": f"Bearer {config.api_key}",
        },
        timeout_seconds=config.timeout_seconds,
    )
    output = response_payload.get("output", {}) if isinstance(response_payload, dict) else {}
    choices = output.get("choices")
    if not isinstance(choices, list) or not choices:
        raise RuntimeError("dashscope response did not include output choices")
    message = choices[0].get("message") if isinstance(choices[0], dict) else None
    content = message.get("content") if isinstance(message, dict) else None
    if not isinstance(content, list) or not content:
        raise RuntimeError("dashscope response did not include image content")
    image_url = content[0].get("image") if isinstance(content[0], dict) else None
    if not isinstance(image_url, str) or not image_url.strip():
        raise RuntimeError("dashscope response did not include a valid image url")
    return image_url.strip()


def _poll_dashscope_image_task(
    task_id: str,
    *,
    config: StandardDishImageGenerationConfig,
) -> str:
    deadline = time.monotonic() + config.timeout_seconds
    endpoint = f"{_get_dashscope_api_origin(config.base_url)}/api/v1/tasks/{task_id}"

    while True:
        task_result = _open_json_request(
            endpoint,
            payload=None,
            headers={
                "Authorization": f"Bearer {config.api_key}",
            },
            method="GET",
            timeout_seconds=config.timeout_seconds,
        )
        output = task_result.get("output", {}) if isinstance(task_result, dict) else {}
        task_status = str(output.get("task_status", "")).strip().upper()

        if task_status == "SUCCEEDED":
            results = output.get("results")
            if not isinstance(results, list) or not results:
                raise RuntimeError("dashscope task completed without image results")
            image_url = results[0].get("url") if isinstance(results[0], dict) else None
            if not isinstance(image_url, str) or not image_url.strip():
                raise RuntimeError("dashscope task result did not include a valid image url")
            return image_url.strip()

        if task_status in {"FAILED", "CANCELED", "UNKNOWN"}:
            message = output.get("message")
            code = output.get("code")
            detail = " ".join(
                str(part).strip()
                for part in (code, message)
                if isinstance(part, str) and part.strip()
            ).strip()
            raise RuntimeError(detail or f"dashscope task ended with status {task_status.lower()}")

        if task_status not in {"PENDING", "RUNNING"}:
            raise RuntimeError(
                f"dashscope task returned unexpected status {task_status or 'empty'}"
            )

        if time.monotonic() >= deadline:
            raise TimeoutError("dashscope image generation task timed out")

        time.sleep(2)


def _get_dashscope_api_origin(base_url: str) -> str:
    parsed = urlparse(base_url.strip())
    if not parsed.scheme or not parsed.netloc:
        raise RuntimeError("invalid dashscope base url")
    return f"{parsed.scheme}://{parsed.netloc}"


def _resolve_dashscope_image_size(model: str) -> str:
    normalized_model = model.strip().lower()
    if normalized_model.startswith("qwen-image-2.0"):
        return "2048*2048"
    return "1328*1328"


def _should_use_dashscope_multimodal_sync_api(model: str) -> bool:
    normalized_model = model.strip().lower()
    return normalized_model.startswith("qwen-image-2.0") or normalized_model.startswith(
        "qwen-image-max"
    )


def _extract_local_generated_asset_filename(image_url: str) -> str | None:
    parsed = urlparse(image_url.strip())
    normalized_path = parsed.path.strip()
    expected_prefix = "/generated-assets/standard-dish-images/"
    if not normalized_path.startswith(expected_prefix):
        return None
    file_name = Path(normalized_path).name
    if not file_name:
        return None
    return file_name


def _resolve_image_file_extension(*, content_type: str, source_url: str) -> str:
    normalized_content_type = content_type.split(";", 1)[0].strip().lower()
    guessed_from_type = mimetypes.guess_extension(normalized_content_type)
    if guessed_from_type:
        return ".jpg" if guessed_from_type == ".jpe" else guessed_from_type

    parsed = urlparse(source_url)
    source_suffix = Path(parsed.path).suffix.strip().lower()
    if source_suffix in {".png", ".jpg", ".jpeg", ".webp"}:
        return ".jpg" if source_suffix == ".jpeg" else source_suffix

    return ".png"


def _extract_http_error_detail(exc: error.HTTPError) -> str:
    detail = ""
    try:
        payload = json.load(exc)
        if isinstance(payload, dict):
            detail = " ".join(
                str(part).strip()
                for part in (
                    payload.get("code"),
                    payload.get("message"),
                )
                if isinstance(part, str) and part.strip()
            ).strip()
    except Exception:
        detail = ""
    return detail or _stringify_exception(exc)


def _open_json_request(
    url: str,
    *,
    payload: dict[str, object] | None,
    headers: dict[str, str],
    timeout_seconds: int,
    method: str = "POST",
) -> dict[str, object]:
    merged_headers = {
        "Content-Type": "application/json",
        **headers,
    }
    body = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = request.Request(
        url,
        data=body,
        headers=merged_headers,
        method=method,
    )
    try:
        with request.urlopen(req, timeout=timeout_seconds) as response:
            data = json.load(response)
    except error.HTTPError as exc:
        raise RuntimeError(_extract_http_error_detail(exc)) from exc
    except error.URLError as exc:
        reason = getattr(exc, "reason", None)
        if isinstance(reason, TimeoutError):
            raise TimeoutError("image generation request timed out") from exc
        raise RuntimeError(_stringify_exception(exc)) from exc

    if not isinstance(data, dict):
        raise RuntimeError("image generation response was not a valid json object")
    return data


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
