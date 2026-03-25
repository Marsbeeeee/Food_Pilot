import sqlite3
from datetime import UTC, datetime

from backend.repositories.standard_dish_repository import get_standard_dish_by_id


IMAGE_GENERATION_JOB_STATUS_QUEUED = "queued"
IMAGE_GENERATION_JOB_STATUS_RUNNING = "running"
IMAGE_GENERATION_JOB_STATUS_COMPLETED = "completed"
IMAGE_GENERATION_JOB_STATUS_FAILED = "failed"
IMAGE_GENERATION_JOB_STATUS_TIMED_OUT = "timed_out"
ACTIVE_IMAGE_GENERATION_JOB_STATUSES = (
    IMAGE_GENERATION_JOB_STATUS_QUEUED,
    IMAGE_GENERATION_JOB_STATUS_RUNNING,
)
TERMINAL_IMAGE_GENERATION_JOB_STATUSES = (
    IMAGE_GENERATION_JOB_STATUS_COMPLETED,
    IMAGE_GENERATION_JOB_STATUS_FAILED,
    IMAGE_GENERATION_JOB_STATUS_TIMED_OUT,
)

IMAGE_GENERATION_JOB_SELECT_COLUMNS = """
    id,
    standard_dish_id,
    dish_image_id,
    retry_of_job_id,
    status,
    prompt_version,
    prompt_text,
    error_message,
    created_at,
    updated_at,
    started_at,
    finished_at
"""


def get_image_generation_job_by_id(
    conn: sqlite3.Connection,
    job_id: int,
) -> dict[str, object] | None:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            {IMAGE_GENERATION_JOB_SELECT_COLUMNS}
        FROM image_generation_jobs
        WHERE id = ?
        """,
        (job_id,),
    )
    return _row_to_image_generation_job(cursor.fetchone())


def list_image_generation_jobs_by_standard_dish(
    conn: sqlite3.Connection,
    standard_dish_id: int,
) -> list[dict[str, object]]:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            {IMAGE_GENERATION_JOB_SELECT_COLUMNS}
        FROM image_generation_jobs
        WHERE standard_dish_id = ?
        ORDER BY created_at DESC, id DESC
        """,
        (standard_dish_id,),
    )
    return [_row_to_image_generation_job(row) for row in cursor.fetchall()]


def list_image_generation_jobs_by_status(
    conn: sqlite3.Connection,
    status: str,
    *,
    limit: int | None = None,
) -> list[dict[str, object]]:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            {IMAGE_GENERATION_JOB_SELECT_COLUMNS}
        FROM image_generation_jobs
        WHERE status = ?
        ORDER BY created_at ASC, id ASC
        LIMIT COALESCE(?, -1)
        """,
        (status, limit),
    )
    return [_row_to_image_generation_job(row) for row in cursor.fetchall()]


def get_active_image_generation_job(
    conn: sqlite3.Connection,
    standard_dish_id: int,
) -> dict[str, object] | None:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            {IMAGE_GENERATION_JOB_SELECT_COLUMNS}
        FROM image_generation_jobs
        WHERE standard_dish_id = ?
          AND status IN (?, ?)
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (
            standard_dish_id,
            IMAGE_GENERATION_JOB_STATUS_QUEUED,
            IMAGE_GENERATION_JOB_STATUS_RUNNING,
        ),
    )
    return _row_to_image_generation_job(cursor.fetchone())


def create_image_generation_job(
    conn: sqlite3.Connection,
    standard_dish_id: int,
    *,
    prompt_version: str,
    prompt_text: str,
    retry_of_job_id: int | None = None,
    auto_commit: bool = True,
) -> dict[str, object]:
    standard_dish = get_standard_dish_by_id(conn, standard_dish_id)
    if standard_dish is None:
        raise LookupError("standard dish not found")

    normalized_prompt_version = _normalize_required_text(prompt_version, "prompt_version")
    normalized_prompt_text = _normalize_required_text(prompt_text, "prompt_text")
    active_job = get_active_image_generation_job(conn, standard_dish_id)
    if active_job is not None:
        return active_job

    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO image_generation_jobs (
                standard_dish_id,
                retry_of_job_id,
                status,
                prompt_version,
                prompt_text
            ) VALUES (?, ?, ?, ?, ?)
            """,
            (
                standard_dish_id,
                retry_of_job_id,
                IMAGE_GENERATION_JOB_STATUS_QUEUED,
                normalized_prompt_version,
                normalized_prompt_text,
            ),
        )
    except sqlite3.IntegrityError:
        active_job = get_active_image_generation_job(conn, standard_dish_id)
        if active_job is not None:
            return active_job
        raise

    if auto_commit:
        conn.commit()
    job = get_image_generation_job_by_id(conn, int(cursor.lastrowid))
    if job is None:
        raise LookupError("image generation job not found after insert")
    return job


def mark_image_generation_job_running(
    conn: sqlite3.Connection,
    job_id: int,
    *,
    auto_commit: bool = True,
) -> dict[str, object]:
    started_at = _current_timestamp()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE image_generation_jobs
        SET
            status = ?,
            started_at = ?,
            finished_at = NULL,
            error_message = NULL
        WHERE id = ?
          AND status = ?
        """,
        (
            IMAGE_GENERATION_JOB_STATUS_RUNNING,
            started_at,
            job_id,
            IMAGE_GENERATION_JOB_STATUS_QUEUED,
        ),
    )
    if cursor.rowcount == 0:
        existing = get_image_generation_job_by_id(conn, job_id)
        if existing is None:
            raise LookupError("image generation job not found")
        return existing

    if auto_commit:
        conn.commit()
    job = get_image_generation_job_by_id(conn, job_id)
    if job is None:
        raise LookupError("image generation job not found after start")
    return job


def mark_image_generation_job_completed(
    conn: sqlite3.Connection,
    job_id: int,
    *,
    dish_image_id: int,
    auto_commit: bool = True,
) -> dict[str, object]:
    return _complete_image_generation_job(
        conn,
        job_id,
        status=IMAGE_GENERATION_JOB_STATUS_COMPLETED,
        dish_image_id=dish_image_id,
        error_message=None,
        auto_commit=auto_commit,
    )


def mark_image_generation_job_failed(
    conn: sqlite3.Connection,
    job_id: int,
    *,
    error_message: str,
    status: str = IMAGE_GENERATION_JOB_STATUS_FAILED,
    auto_commit: bool = True,
) -> dict[str, object]:
    if status not in {
        IMAGE_GENERATION_JOB_STATUS_FAILED,
        IMAGE_GENERATION_JOB_STATUS_TIMED_OUT,
    }:
        raise ValueError("invalid terminal job status")
    return _complete_image_generation_job(
        conn,
        job_id,
        status=status,
        dish_image_id=None,
        error_message=error_message,
        auto_commit=auto_commit,
    )


def retry_image_generation_job(
    conn: sqlite3.Connection,
    job_id: int,
    *,
    auto_commit: bool = True,
) -> dict[str, object]:
    job = get_image_generation_job_by_id(conn, job_id)
    if job is None:
        raise LookupError("image generation job not found")
    if job["status"] not in {
        IMAGE_GENERATION_JOB_STATUS_FAILED,
        IMAGE_GENERATION_JOB_STATUS_TIMED_OUT,
    }:
        raise ValueError("only failed or timed out jobs can be retried")

    return create_image_generation_job(
        conn,
        int(job["standard_dish_id"]),
        prompt_version=str(job["prompt_version"]),
        prompt_text=str(job["prompt_text"]),
        retry_of_job_id=int(job["id"]),
        auto_commit=auto_commit,
    )


def mark_running_image_generation_jobs_timed_out(
    conn: sqlite3.Connection,
    *,
    error_message: str,
    auto_commit: bool = True,
) -> int:
    normalized_error = _normalize_required_text(error_message, "error_message")
    finished_at = _current_timestamp()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE image_generation_jobs
        SET
            status = ?,
            error_message = ?,
            finished_at = ?
        WHERE status = ?
        """,
        (
            IMAGE_GENERATION_JOB_STATUS_TIMED_OUT,
            normalized_error,
            finished_at,
            IMAGE_GENERATION_JOB_STATUS_RUNNING,
        ),
    )
    updated_count = int(cursor.rowcount)
    if auto_commit:
        conn.commit()
    return updated_count


def _complete_image_generation_job(
    conn: sqlite3.Connection,
    job_id: int,
    *,
    status: str,
    dish_image_id: int | None,
    error_message: str | None,
    auto_commit: bool,
) -> dict[str, object]:
    finished_at = _current_timestamp()
    normalized_error_message = _normalize_optional_text(error_message)
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE image_generation_jobs
        SET
            status = ?,
            dish_image_id = ?,
            error_message = ?,
            started_at = COALESCE(started_at, ?),
            finished_at = ?
        WHERE id = ?
          AND status IN (?, ?)
        """,
        (
            status,
            dish_image_id,
            normalized_error_message,
            finished_at,
            finished_at,
            job_id,
            IMAGE_GENERATION_JOB_STATUS_QUEUED,
            IMAGE_GENERATION_JOB_STATUS_RUNNING,
        ),
    )
    if cursor.rowcount == 0:
        existing = get_image_generation_job_by_id(conn, job_id)
        if existing is None:
            raise LookupError("image generation job not found")
        return existing

    if auto_commit:
        conn.commit()
    job = get_image_generation_job_by_id(conn, job_id)
    if job is None:
        raise LookupError("image generation job not found after completion")
    return job


def _row_to_image_generation_job(row: sqlite3.Row | None) -> dict[str, object] | None:
    if row is None:
        return None
    return dict(row)


def _normalize_required_text(value: str, field_name: str) -> str:
    normalized = value.strip()
    if not normalized:
        raise ValueError(f"{field_name} is required")
    return normalized


def _normalize_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    normalized = value.strip()
    return normalized or None


def _current_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
