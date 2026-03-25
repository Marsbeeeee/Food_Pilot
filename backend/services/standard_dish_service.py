from backend.database.connection import get_db_connection
from backend.repositories.standard_dish_repository import (
    approve_dish_image_candidate as approve_dish_image_candidate_record,
    can_trigger_standard_dish_image_generation as can_trigger_standard_dish_image_generation_record,
    create_dish_image_candidate as create_dish_image_candidate_record,
    get_or_create_standard_dish as get_or_create_standard_dish_record,
    get_standard_dish_by_id as get_standard_dish_by_id_record,
    get_standard_dish_by_name as get_standard_dish_by_name_record,
    list_dish_images_by_standard_dish as list_dish_images_by_standard_dish_record,
    list_standard_dishes_ready_for_image_generation as list_standard_dishes_ready_for_image_generation_record,
    reject_dish_image_candidate as reject_dish_image_candidate_record,
)


def get_or_create_standard_dish(canonical_name: str) -> dict[str, object]:
    conn = get_db_connection()
    try:
        return get_or_create_standard_dish_record(conn, canonical_name)
    finally:
        conn.close()


def get_standard_dish_by_id(standard_dish_id: int) -> dict[str, object] | None:
    conn = get_db_connection()
    try:
        return get_standard_dish_by_id_record(conn, standard_dish_id)
    finally:
        conn.close()


def get_standard_dish_by_name(canonical_name: str) -> dict[str, object] | None:
    conn = get_db_connection()
    try:
        return get_standard_dish_by_name_record(conn, canonical_name)
    finally:
        conn.close()


def list_standard_dishes_ready_for_image_generation(
    *,
    limit: int | None = None,
) -> list[dict[str, object]]:
    conn = get_db_connection()
    try:
        return list_standard_dishes_ready_for_image_generation_record(conn, limit=limit)
    finally:
        conn.close()


def can_trigger_standard_dish_image_generation(standard_dish_id: int) -> bool:
    conn = get_db_connection()
    try:
        return can_trigger_standard_dish_image_generation_record(conn, standard_dish_id)
    finally:
        conn.close()


def create_dish_image_candidate(
    standard_dish_id: int,
    *,
    image_url: str,
    prompt_version: str | None = None,
) -> dict[str, object]:
    conn = get_db_connection()
    try:
        return create_dish_image_candidate_record(
            conn,
            standard_dish_id,
            image_url=image_url,
            prompt_version=prompt_version,
        )
    finally:
        conn.close()


def approve_dish_image_candidate(
    standard_dish_id: int,
    dish_image_id: int,
) -> dict[str, object]:
    conn = get_db_connection()
    try:
        return approve_dish_image_candidate_record(conn, standard_dish_id, dish_image_id)
    finally:
        conn.close()


def reject_dish_image_candidate(
    standard_dish_id: int,
    dish_image_id: int,
    *,
    review_note: str | None = None,
) -> dict[str, object]:
    conn = get_db_connection()
    try:
        return reject_dish_image_candidate_record(
            conn,
            standard_dish_id,
            dish_image_id,
            review_note=review_note,
        )
    finally:
        conn.close()


def list_dish_images_by_standard_dish(
    standard_dish_id: int,
) -> list[dict[str, object]]:
    conn = get_db_connection()
    try:
        return list_dish_images_by_standard_dish_record(conn, standard_dish_id)
    finally:
        conn.close()
