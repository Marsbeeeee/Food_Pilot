import sqlite3
from datetime import UTC, datetime

from backend.text import normalize_food_log_query


PENDING_IMAGE_STATUS = "pending"
APPROVED_IMAGE_STATUS = "approved"
REJECTED_IMAGE_STATUS = "rejected"

STANDARD_DISH_SELECT_COLUMNS = """
    id,
    canonical_name,
    normalized_name,
    image_url,
    image_status,
    image_prompt_version,
    image_updated_at,
    created_at,
    updated_at
"""

DISH_IMAGE_SELECT_COLUMNS = """
    id,
    standard_dish_id,
    image_url,
    status,
    prompt_version,
    review_note,
    reviewed_by_user_id,
    created_at,
    updated_at,
    reviewed_at
"""

DISH_IMAGE_SELECT_COLUMNS_WITH_ALIAS = """
    dish_images.id AS id,
    dish_images.standard_dish_id AS standard_dish_id,
    dish_images.image_url AS image_url,
    dish_images.status AS status,
    dish_images.prompt_version AS prompt_version,
    dish_images.review_note AS review_note,
    dish_images.reviewed_by_user_id AS reviewed_by_user_id,
    dish_images.created_at AS created_at,
    dish_images.updated_at AS updated_at,
    dish_images.reviewed_at AS reviewed_at
"""


def get_or_create_standard_dish(
    conn: sqlite3.Connection,
    canonical_name: str,
    *,
    auto_commit: bool = True,
) -> dict[str, object]:
    normalized_name = _normalize_standard_dish_name(canonical_name)
    existing = get_standard_dish_by_name(conn, canonical_name)
    if existing is not None:
        return existing

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO standard_dishes (
            canonical_name,
            normalized_name
        ) VALUES (?, ?)
        """,
        (canonical_name.strip(), normalized_name),
    )
    if auto_commit:
        conn.commit()
    standard_dish = get_standard_dish_by_id(conn, int(cursor.lastrowid))
    if standard_dish is None:
        raise LookupError("standard dish not found after insert")
    return standard_dish


def get_standard_dish_by_id(
    conn: sqlite3.Connection,
    standard_dish_id: int,
) -> dict[str, object] | None:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            {STANDARD_DISH_SELECT_COLUMNS}
        FROM standard_dishes
        WHERE id = ?
        """,
        (standard_dish_id,),
    )
    return _row_to_standard_dish(conn, cursor.fetchone())


def get_standard_dish_by_name(
    conn: sqlite3.Connection,
    canonical_name: str,
) -> dict[str, object] | None:
    normalized_name = _normalize_standard_dish_name(canonical_name)
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            {STANDARD_DISH_SELECT_COLUMNS}
        FROM standard_dishes
        WHERE normalized_name = ?
        ORDER BY id DESC
        LIMIT 1
        """,
        (normalized_name,),
    )
    return _row_to_standard_dish(conn, cursor.fetchone())


def list_standard_dishes_ready_for_image_generation(
    conn: sqlite3.Connection,
    *,
    limit: int | None = None,
) -> list[dict[str, object]]:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            {STANDARD_DISH_SELECT_COLUMNS}
        FROM standard_dishes
        WHERE (image_url IS NULL OR trim(image_url) = '')
          AND COALESCE(image_status, '') != ?
          AND id NOT IN (
              SELECT standard_dish_id
              FROM image_generation_jobs
              WHERE status IN ('queued', 'running')
          )
        ORDER BY updated_at DESC, id DESC
        LIMIT COALESCE(?, -1)
        """,
        (PENDING_IMAGE_STATUS, limit),
    )
    return [_row_to_standard_dish(conn, row) for row in cursor.fetchall()]


def can_trigger_standard_dish_image_generation(
    conn: sqlite3.Connection,
    standard_dish_id: int,
) -> bool:
    standard_dish = get_standard_dish_by_id(conn, standard_dish_id)
    if standard_dish is None:
        raise LookupError("standard dish not found")
    return bool(standard_dish["can_trigger_image_generation"])


def create_dish_image_candidate(
    conn: sqlite3.Connection,
    standard_dish_id: int,
    *,
    image_url: str,
    prompt_version: str | None = None,
    auto_commit: bool = True,
) -> dict[str, object]:
    standard_dish = get_standard_dish_by_id(conn, standard_dish_id)
    if standard_dish is None:
        raise LookupError("standard dish not found")

    normalized_image_url = _normalize_required_text(image_url, "image_url")
    normalized_prompt_version = _normalize_optional_text(prompt_version)
    pending_image = _get_pending_dish_image(conn, standard_dish_id)
    if pending_image is not None:
        if (
            pending_image["image_url"] == normalized_image_url
            and pending_image["prompt_version"] == normalized_prompt_version
        ):
            return pending_image
        raise ValueError("standard dish already has a pending image candidate")

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO dish_images (
            standard_dish_id,
            image_url,
            status,
            prompt_version
        ) VALUES (?, ?, ?, ?)
        """,
        (
            standard_dish_id,
            normalized_image_url,
            PENDING_IMAGE_STATUS,
            normalized_prompt_version,
        ),
    )

    if not _has_official_image(standard_dish):
        reviewed_at = _current_timestamp()
        cursor.execute(
            """
            UPDATE standard_dishes
            SET
                image_status = ?,
                image_prompt_version = ?,
                image_updated_at = ?
            WHERE id = ?
            """,
            (
                PENDING_IMAGE_STATUS,
                normalized_prompt_version,
                reviewed_at,
                standard_dish_id,
            ),
        )

    if auto_commit:
        conn.commit()
    dish_image = get_dish_image_by_id(conn, int(cursor.lastrowid))
    if dish_image is None:
        raise LookupError("dish image not found after insert")
    return dish_image


def get_dish_image_by_id(
    conn: sqlite3.Connection,
    dish_image_id: int,
) -> dict[str, object] | None:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            {DISH_IMAGE_SELECT_COLUMNS}
        FROM dish_images
        WHERE id = ?
        """,
        (dish_image_id,),
    )
    return _row_to_dish_image(cursor.fetchone())


def list_dish_images_by_standard_dish(
    conn: sqlite3.Connection,
    standard_dish_id: int,
) -> list[dict[str, object]]:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            {DISH_IMAGE_SELECT_COLUMNS}
        FROM dish_images
        WHERE standard_dish_id = ?
        ORDER BY created_at DESC, id DESC
        """,
        (standard_dish_id,),
    )
    return [_row_to_dish_image(row) for row in cursor.fetchall()]


def list_dish_image_candidates(
    conn: sqlite3.Connection,
    *,
    status: str | None = None,
    query: str | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
    limit: int | None = None,
) -> list[dict[str, object]]:
    normalized_query = _normalize_optional_text(query)
    normalized_status = _normalize_optional_text(status)
    if normalized_status is not None and normalized_status not in {
        PENDING_IMAGE_STATUS,
        APPROVED_IMAGE_STATUS,
        REJECTED_IMAGE_STATUS,
    }:
        raise ValueError("invalid dish image status")

    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            {DISH_IMAGE_SELECT_COLUMNS_WITH_ALIAS},
            standard_dishes.canonical_name AS standard_dish_name,
            standard_dishes.image_url AS official_image_url,
            standard_dishes.image_status AS official_image_status
        FROM dish_images
        JOIN standard_dishes
          ON standard_dishes.id = dish_images.standard_dish_id
        WHERE (? IS NULL OR dish_images.status = ?)
          AND (
              ? IS NULL
              OR standard_dishes.canonical_name LIKE '%' || ? || '%'
              OR standard_dishes.normalized_name LIKE '%' || ? || '%'
          )
          AND (? IS NULL OR dish_images.created_at >= ?)
          AND (? IS NULL OR dish_images.created_at < datetime(?, '+1 day'))
        ORDER BY dish_images.created_at DESC, dish_images.id DESC
        LIMIT COALESCE(?, -1)
        """,
        (
            normalized_status,
            normalized_status,
            normalized_query,
            normalized_query,
            normalized_query,
            created_from,
            created_from,
            created_to,
            created_to,
            limit,
        ),
    )
    return [dict(row) for row in cursor.fetchall()]


def get_dish_image_candidate_detail(
    conn: sqlite3.Connection,
    dish_image_id: int,
) -> dict[str, object] | None:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            {DISH_IMAGE_SELECT_COLUMNS_WITH_ALIAS},
            standard_dishes.canonical_name AS standard_dish_name,
            standard_dishes.image_url AS official_image_url,
            standard_dishes.image_status AS official_image_status,
            standard_dishes.image_prompt_version AS official_image_prompt_version,
            standard_dishes.image_updated_at AS official_image_updated_at
        FROM dish_images
        JOIN standard_dishes
          ON standard_dishes.id = dish_images.standard_dish_id
        WHERE dish_images.id = ?
        """,
        (dish_image_id,),
    )
    row = cursor.fetchone()
    return dict(row) if row is not None else None


def list_dish_image_admin_events(
    conn: sqlite3.Connection,
    *,
    standard_dish_id: int,
    limit: int | None = None,
) -> list[dict[str, object]]:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            events.id,
            events.standard_dish_id,
            events.dish_image_id,
            events.actor_user_id,
            users.display_name AS actor_display_name,
            users.email AS actor_email,
            events.action,
            events.result_status,
            events.note,
            events.created_at
        FROM dish_image_admin_events AS events
        JOIN users
          ON users.id = events.actor_user_id
        WHERE events.standard_dish_id = ?
        ORDER BY events.created_at DESC, events.id DESC
        LIMIT COALESCE(?, -1)
        """,
        (standard_dish_id, limit),
    )
    return [dict(row) for row in cursor.fetchall()]


def create_dish_image_admin_event(
    conn: sqlite3.Connection,
    *,
    standard_dish_id: int,
    actor_user_id: int,
    action: str,
    result_status: str,
    dish_image_id: int | None = None,
    note: str | None = None,
    auto_commit: bool = True,
) -> dict[str, object]:
    normalized_action = _normalize_required_text(action, "action")
    if normalized_action not in {"approve", "reject", "regenerate"}:
        raise ValueError("invalid admin dish image action")

    normalized_result_status = _normalize_required_text(result_status, "result_status")
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO dish_image_admin_events (
            standard_dish_id,
            dish_image_id,
            actor_user_id,
            action,
            result_status,
            note
        ) VALUES (?, ?, ?, ?, ?, ?)
        """,
        (
            standard_dish_id,
            dish_image_id,
            actor_user_id,
            normalized_action,
            normalized_result_status,
            _normalize_optional_text(note),
        ),
    )
    if auto_commit:
        conn.commit()
    event_id = int(cursor.lastrowid)
    return list_dish_image_admin_events(
        conn,
        standard_dish_id=standard_dish_id,
        limit=1,
    )[0]


def approve_dish_image_candidate(
    conn: sqlite3.Connection,
    standard_dish_id: int,
    dish_image_id: int,
    *,
    reviewed_by_user_id: int | None = None,
    review_note: str | None = None,
    auto_commit: bool = True,
) -> dict[str, object]:
    standard_dish = get_standard_dish_by_id(conn, standard_dish_id)
    if standard_dish is None:
        raise LookupError("standard dish not found")

    dish_image = _get_dish_image_for_standard_dish(conn, standard_dish_id, dish_image_id)
    if dish_image is None:
        raise LookupError("dish image candidate not found")

    if dish_image["status"] == REJECTED_IMAGE_STATUS:
        raise ValueError("rejected image candidate cannot be approved")

    approved_image = _get_approved_dish_image(conn, standard_dish_id)
    reviewed_at = _current_timestamp()
    cursor = conn.cursor()
    normalized_review_note = _normalize_optional_text(review_note)
    if approved_image is not None and int(approved_image["id"]) != dish_image_id:
        cursor.execute(
            """
            UPDATE dish_images
            SET
                status = ?,
                review_note = ?,
                reviewed_by_user_id = ?,
                reviewed_at = ?
            WHERE id = ?
            """,
            (
                REJECTED_IMAGE_STATUS,
                "Superseded by a newer approved candidate",
                reviewed_by_user_id,
                reviewed_at,
                int(approved_image["id"]),
            ),
        )
    cursor.execute(
        """
        UPDATE dish_images
        SET
            status = ?,
            review_note = ?,
            reviewed_by_user_id = ?,
            reviewed_at = ?
        WHERE id = ?
        """,
        (
            APPROVED_IMAGE_STATUS,
            normalized_review_note,
            reviewed_by_user_id,
            reviewed_at,
            dish_image_id,
        ),
    )
    cursor.execute(
        """
        UPDATE standard_dishes
        SET
            image_url = ?,
            image_status = ?,
            image_prompt_version = ?,
            image_updated_at = ?
        WHERE id = ?
        """,
        (
            dish_image["image_url"],
            APPROVED_IMAGE_STATUS,
            dish_image["prompt_version"],
            reviewed_at,
            standard_dish_id,
        ),
    )

    if auto_commit:
        conn.commit()
    updated = get_standard_dish_by_id(conn, standard_dish_id)
    if updated is None:
        raise LookupError("standard dish not found after approval")
    return updated


def reject_dish_image_candidate(
    conn: sqlite3.Connection,
    standard_dish_id: int,
    dish_image_id: int,
    *,
    reviewed_by_user_id: int | None = None,
    review_note: str | None = None,
    auto_commit: bool = True,
) -> dict[str, object]:
    standard_dish = get_standard_dish_by_id(conn, standard_dish_id)
    if standard_dish is None:
        raise LookupError("standard dish not found")

    dish_image = _get_dish_image_for_standard_dish(conn, standard_dish_id, dish_image_id)
    if dish_image is None:
        raise LookupError("dish image candidate not found")

    if dish_image["status"] == APPROVED_IMAGE_STATUS and _has_official_image(standard_dish):
        raise ValueError("cannot reject the current official image")

    reviewed_at = _current_timestamp()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE dish_images
        SET
            status = ?,
            review_note = ?,
            reviewed_by_user_id = ?,
            reviewed_at = ?
        WHERE id = ?
        """,
        (
            REJECTED_IMAGE_STATUS,
            _normalize_optional_text(review_note),
            reviewed_by_user_id,
            reviewed_at,
            dish_image_id,
        ),
    )

    if not _has_official_image(standard_dish):
        cursor.execute(
            """
            UPDATE standard_dishes
            SET
                image_url = NULL,
                image_status = ?,
                image_prompt_version = ?,
                image_updated_at = ?
            WHERE id = ?
            """,
            (
                REJECTED_IMAGE_STATUS,
                dish_image["prompt_version"],
                reviewed_at,
                standard_dish_id,
            ),
        )

    if auto_commit:
        conn.commit()
    updated = get_standard_dish_by_id(conn, standard_dish_id)
    if updated is None:
        raise LookupError("standard dish not found after rejection")
    return updated


def _get_pending_dish_image(
    conn: sqlite3.Connection,
    standard_dish_id: int,
) -> dict[str, object] | None:
    return _get_single_dish_image_by_status(conn, standard_dish_id, PENDING_IMAGE_STATUS)


def _get_approved_dish_image(
    conn: sqlite3.Connection,
    standard_dish_id: int,
) -> dict[str, object] | None:
    return _get_single_dish_image_by_status(conn, standard_dish_id, APPROVED_IMAGE_STATUS)


def get_pending_dish_image(
    conn: sqlite3.Connection,
    standard_dish_id: int,
) -> dict[str, object] | None:
    return _get_pending_dish_image(conn, standard_dish_id)


def get_approved_dish_image(
    conn: sqlite3.Connection,
    standard_dish_id: int,
) -> dict[str, object] | None:
    return _get_approved_dish_image(conn, standard_dish_id)


def _get_single_dish_image_by_status(
    conn: sqlite3.Connection,
    standard_dish_id: int,
    status: str,
) -> dict[str, object] | None:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            {DISH_IMAGE_SELECT_COLUMNS}
        FROM dish_images
        WHERE standard_dish_id = ? AND status = ?
        ORDER BY created_at DESC, id DESC
        LIMIT 1
        """,
        (standard_dish_id, status),
    )
    return _row_to_dish_image(cursor.fetchone())


def _get_dish_image_for_standard_dish(
    conn: sqlite3.Connection,
    standard_dish_id: int,
    dish_image_id: int,
) -> dict[str, object] | None:
    cursor = conn.cursor()
    cursor.execute(
        f"""
        SELECT
            {DISH_IMAGE_SELECT_COLUMNS}
        FROM dish_images
        WHERE id = ? AND standard_dish_id = ?
        """,
        (dish_image_id, standard_dish_id),
    )
    return _row_to_dish_image(cursor.fetchone())


def _row_to_standard_dish(
    conn: sqlite3.Connection,
    row: sqlite3.Row | None,
) -> dict[str, object] | None:
    if row is None:
        return None
    standard_dish = dict(row)
    standard_dish["has_official_image"] = _has_official_image(standard_dish)
    standard_dish["has_active_image_generation_job"] = _has_active_image_generation_job(
        conn,
        int(standard_dish["id"]),
    )
    standard_dish["can_trigger_image_generation"] = (
        not standard_dish["has_official_image"]
        and standard_dish.get("image_status") != PENDING_IMAGE_STATUS
        and not standard_dish["has_active_image_generation_job"]
    )
    return standard_dish


def _row_to_dish_image(row: sqlite3.Row | None) -> dict[str, object] | None:
    if row is None:
        return None
    return dict(row)


def _normalize_standard_dish_name(value: str) -> str:
    normalized = normalize_food_log_query(value)
    if not normalized:
        raise ValueError("canonical_name is required")
    return normalized


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


def _has_official_image(standard_dish: dict[str, object]) -> bool:
    image_url = standard_dish.get("image_url")
    image_status = standard_dish.get("image_status")
    return (
        isinstance(image_url, str)
        and bool(image_url.strip())
        and image_status == APPROVED_IMAGE_STATUS
    )


def _has_active_image_generation_job(
    conn: sqlite3.Connection,
    standard_dish_id: int,
) -> bool:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT 1
        FROM image_generation_jobs
        WHERE standard_dish_id = ?
          AND status IN ('queued', 'running')
        LIMIT 1
        """,
        (standard_dish_id,),
    )
    return cursor.fetchone() is not None


def _current_timestamp() -> str:
    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")
