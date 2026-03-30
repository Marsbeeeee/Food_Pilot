from backend.database.connection import get_db_connection
from backend.repositories.image_generation_job_repository import (
    IMAGE_GENERATION_JOB_STATUS_QUEUED,
    IMAGE_GENERATION_JOB_STATUS_RUNNING,
    get_active_image_generation_job,
    list_image_generation_jobs_by_status,
)
from backend.repositories.standard_dish_repository import (
    APPROVED_IMAGE_STATUS,
    PENDING_IMAGE_STATUS,
    REJECTED_IMAGE_STATUS,
    approve_dish_image_candidate,
    create_dish_image_admin_event,
    get_approved_dish_image,
    get_dish_image_candidate_detail,
    get_pending_dish_image,
    get_standard_dish_by_id,
    list_dish_image_admin_events,
    list_dish_image_candidates,
    reject_dish_image_candidate,
)
from backend.services.standard_dish_image_generation_service import (
    cleanup_local_standard_dish_image_asset_if_unreferenced,
    dispatch_image_generation_job,
    enqueue_admin_standard_dish_image_regeneration,
)


def list_admin_dish_image_candidates(
    *,
    status: str | None = None,
    query: str | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
    limit: int = 50,
) -> list[dict[str, object]]:
    conn = get_db_connection()
    try:
        candidates = list_dish_image_candidates(
            conn,
            status=status,
            query=query,
            created_from=created_from,
            created_to=created_to,
            limit=limit,
        )
        return [_serialize_candidate_summary(conn, candidate) for candidate in candidates]
    finally:
        conn.close()


def list_admin_active_generation_jobs(
    *,
    limit: int = 50,
) -> list[dict[str, object]]:
    conn = get_db_connection()
    try:
        active_jobs = [
            *list_image_generation_jobs_by_status(
                conn,
                IMAGE_GENERATION_JOB_STATUS_RUNNING,
                limit=limit,
            ),
            *list_image_generation_jobs_by_status(
                conn,
                IMAGE_GENERATION_JOB_STATUS_QUEUED,
                limit=limit,
            ),
        ]
        sorted_jobs = sorted(
            active_jobs,
            key=lambda item: (str(item["created_at"]), int(item["id"])),
            reverse=True,
        )[:limit]
        return [
            _serialize_active_generation_job_entry(conn, job)
            for job in sorted_jobs
        ]
    finally:
        conn.close()


def get_admin_dish_image_candidate(dish_image_id: int) -> dict[str, object] | None:
    conn = get_db_connection()
    try:
        detail = get_dish_image_candidate_detail(conn, dish_image_id)
        if detail is None:
            return None
        return _serialize_candidate_detail(conn, detail)
    finally:
        conn.close()


def approve_admin_dish_image_candidate(
    *,
    admin_user_id: int,
    dish_image_id: int,
    note: str | None = None,
) -> dict[str, object]:
    conn = get_db_connection()
    try:
        detail = get_dish_image_candidate_detail(conn, dish_image_id)
        if detail is None:
            raise LookupError("dish image candidate not found")

        approve_dish_image_candidate(
            conn,
            int(detail["standard_dish_id"]),
            dish_image_id,
            reviewed_by_user_id=admin_user_id,
            review_note=note,
            auto_commit=False,
        )
        create_dish_image_admin_event(
            conn,
            standard_dish_id=int(detail["standard_dish_id"]),
            dish_image_id=dish_image_id,
            actor_user_id=admin_user_id,
            action="approve",
            result_status=APPROVED_IMAGE_STATUS,
            note=note,
            auto_commit=False,
        )
        conn.commit()
        refreshed = get_dish_image_candidate_detail(conn, dish_image_id)
        if refreshed is None:
            raise LookupError("dish image candidate not found after approval")
        return _serialize_candidate_detail(conn, refreshed)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def reject_admin_dish_image_candidate(
    *,
    admin_user_id: int,
    dish_image_id: int,
    note: str | None = None,
) -> dict[str, object]:
    conn = get_db_connection()
    try:
        detail = get_dish_image_candidate_detail(conn, dish_image_id)
        if detail is None:
            raise LookupError("dish image candidate not found")

        reject_dish_image_candidate(
            conn,
            int(detail["standard_dish_id"]),
            dish_image_id,
            reviewed_by_user_id=admin_user_id,
            review_note=note,
            auto_commit=False,
        )
        cleanup_local_standard_dish_image_asset_if_unreferenced(
            str(detail["image_url"]),
            conn=conn,
        )
        create_dish_image_admin_event(
            conn,
            standard_dish_id=int(detail["standard_dish_id"]),
            dish_image_id=dish_image_id,
            actor_user_id=admin_user_id,
            action="reject",
            result_status=REJECTED_IMAGE_STATUS,
            note=note,
            auto_commit=False,
        )
        conn.commit()
        refreshed = get_dish_image_candidate_detail(conn, dish_image_id)
        if refreshed is None:
            raise LookupError("dish image candidate not found after rejection")
        return _serialize_candidate_detail(conn, refreshed)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def regenerate_admin_dish_image_candidate(
    *,
    admin_user_id: int,
    dish_image_id: int,
    note: str | None = None,
) -> dict[str, object]:
    conn = get_db_connection()
    try:
        detail = get_dish_image_candidate_detail(conn, dish_image_id)
        if detail is None:
            raise LookupError("dish image candidate not found")

        job = enqueue_admin_standard_dish_image_regeneration(
            int(detail["standard_dish_id"]),
            conn=conn,
            replace_pending=str(detail["status"]) == PENDING_IMAGE_STATUS,
            reviewed_by_user_id=admin_user_id,
            review_note=note,
            dispatch_async=False,
        )
        create_dish_image_admin_event(
            conn,
            standard_dish_id=int(detail["standard_dish_id"]),
            dish_image_id=dish_image_id,
            actor_user_id=admin_user_id,
            action="regenerate",
            result_status=str(job["status"]),
            note=note,
            auto_commit=False,
        )
        conn.commit()
        dispatch_image_generation_job(int(job["id"]))
        refreshed = _resolve_regenerate_response_candidate(
            conn,
            standard_dish_id=int(detail["standard_dish_id"]),
            fallback_dish_image_id=dish_image_id,
        )
        if refreshed is None:
            raise LookupError("dish image candidate not found after regenerate")
        return _serialize_candidate_detail(conn, refreshed)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def reject_and_regenerate_admin_dish_image_candidate(
    *,
    admin_user_id: int,
    dish_image_id: int,
    note: str | None = None,
) -> dict[str, object]:
    conn = get_db_connection()
    try:
        detail = get_dish_image_candidate_detail(conn, dish_image_id)
        if detail is None:
            raise LookupError("dish image candidate not found")

        reject_dish_image_candidate(
            conn,
            int(detail["standard_dish_id"]),
            dish_image_id,
            reviewed_by_user_id=admin_user_id,
            review_note=note,
            auto_commit=False,
        )
        cleanup_local_standard_dish_image_asset_if_unreferenced(
            str(detail["image_url"]),
            conn=conn,
        )
        job = enqueue_admin_standard_dish_image_regeneration(
            int(detail["standard_dish_id"]),
            conn=conn,
            replace_pending=False,
            reviewed_by_user_id=admin_user_id,
            review_note=note,
            dispatch_async=False,
        )
        create_dish_image_admin_event(
            conn,
            standard_dish_id=int(detail["standard_dish_id"]),
            dish_image_id=dish_image_id,
            actor_user_id=admin_user_id,
            action="reject",
            result_status=REJECTED_IMAGE_STATUS,
            note=note,
            auto_commit=False,
        )
        create_dish_image_admin_event(
            conn,
            standard_dish_id=int(detail["standard_dish_id"]),
            dish_image_id=dish_image_id,
            actor_user_id=admin_user_id,
            action="regenerate",
            result_status=str(job["status"]),
            note=note,
            auto_commit=False,
        )
        conn.commit()
        dispatch_image_generation_job(int(job["id"]))
        refreshed = _resolve_regenerate_response_candidate(
            conn,
            standard_dish_id=int(detail["standard_dish_id"]),
            fallback_dish_image_id=dish_image_id,
        )
        if refreshed is None:
            raise LookupError("dish image candidate not found after regenerate")
        return _serialize_candidate_detail(conn, refreshed)
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def _resolve_regenerate_response_candidate(
    conn,
    *,
    standard_dish_id: int,
    fallback_dish_image_id: int,
) -> dict[str, object] | None:
    pending = get_pending_dish_image(conn, standard_dish_id)
    if pending is not None:
        return get_dish_image_candidate_detail(conn, int(pending["id"]))
    return get_dish_image_candidate_detail(conn, fallback_dish_image_id)


def _serialize_candidate_summary(
    conn,
    candidate: dict[str, object],
) -> dict[str, object]:
    approved_image = get_approved_dish_image(conn, int(candidate["standard_dish_id"]))
    active_generation_job = _serialize_active_generation_job(
        conn,
        standard_dish_id=int(candidate["standard_dish_id"]),
    )
    return {
        "id": int(candidate["id"]),
        "standard_dish_id": int(candidate["standard_dish_id"]),
        "standard_dish_name": str(candidate["standard_dish_name"]),
        "image_url": str(candidate["image_url"]),
        "status": str(candidate["status"]),
        "prompt_version": candidate.get("prompt_version"),
        "review_note": candidate.get("review_note"),
        "created_at": str(candidate["created_at"]),
        "reviewed_at": candidate.get("reviewed_at"),
        "official_image_url": candidate.get("official_image_url"),
        "official_image_status": candidate.get("official_image_status"),
        "is_current_official": (
            approved_image is not None
            and int(approved_image["id"]) == int(candidate["id"])
        ),
        "active_generation_job": active_generation_job,
    }


def _serialize_candidate_detail(
    conn,
    candidate: dict[str, object],
) -> dict[str, object]:
    standard_dish = get_standard_dish_by_id(conn, int(candidate["standard_dish_id"]))
    if standard_dish is None:
        raise LookupError("standard dish not found")
    approved_image = get_approved_dish_image(conn, int(candidate["standard_dish_id"]))
    pending_image = get_pending_dish_image(conn, int(candidate["standard_dish_id"]))
    is_current_official = (
        approved_image is not None
        and int(approved_image["id"]) == int(candidate["id"])
    )
    recent_operations = [
        {
            "id": int(event["id"]),
            "dish_image_id": (
                int(event["dish_image_id"])
                if event.get("dish_image_id") is not None
                else None
            ),
            "action": str(event["action"]),
            "result_status": str(event["result_status"]),
            "note": event.get("note"),
            "created_at": str(event["created_at"]),
            "actor": {
                "id": int(event["actor_user_id"]),
                "display_name": str(event["actor_display_name"]),
                "email": str(event["actor_email"]),
            },
        }
        for event in list_dish_image_admin_events(
            conn,
            standard_dish_id=int(candidate["standard_dish_id"]),
            limit=10,
        )
    ]
    can_regenerate = (
        not bool(standard_dish["has_active_image_generation_job"])
        and (
            pending_image is None
            or int(pending_image["id"]) == int(candidate["id"])
        )
    )
    return {
        **_serialize_candidate_summary(conn, candidate),
        "official_image_prompt_version": standard_dish.get("image_prompt_version"),
        "official_image_updated_at": standard_dish.get("image_updated_at"),
        "can_approve": str(candidate["status"]) != REJECTED_IMAGE_STATUS and not is_current_official,
        "can_reject": str(candidate["status"]) != REJECTED_IMAGE_STATUS and not is_current_official,
        "can_regenerate": can_regenerate,
        "recent_operations": recent_operations,
    }


def _serialize_active_generation_job(
    conn,
    *,
    standard_dish_id: int,
) -> dict[str, object] | None:
    job = get_active_image_generation_job(conn, standard_dish_id)
    if job is None:
        return None
    return {
        "id": int(job["id"]),
        "status": str(job["status"]),
        "created_at": str(job["created_at"]),
        "started_at": (
            str(job["started_at"])
            if job.get("started_at") is not None
            else None
        ),
    }


def _serialize_active_generation_job_entry(
    conn,
    job: dict[str, object],
) -> dict[str, object]:
    standard_dish_id = int(job["standard_dish_id"])
    standard_dish = get_standard_dish_by_id(conn, standard_dish_id)
    if standard_dish is None:
        raise LookupError("standard dish not found for image generation job")
    return {
        "id": int(job["id"]),
        "standard_dish_id": standard_dish_id,
        "standard_dish_name": str(standard_dish["canonical_name"]),
        "status": str(job["status"]),
        "created_at": str(job["created_at"]),
        "started_at": (
            str(job["started_at"])
            if job.get("started_at") is not None
            else None
        ),
    }
