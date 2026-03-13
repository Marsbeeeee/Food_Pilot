from backend.database.connection import get_db_connection
from backend.repositories.profile_repository import (
    create_profile as create_profile_record,
    get_profile as get_profile_record,
    get_profile_by_user_id as get_profile_by_user_id_record,
    update_profile as update_profile_record,
)
from backend.schemas.profile import ProfileIn, ProfileOut


def create_profile(user_id: int, profile: ProfileIn) -> ProfileOut:
    conn = get_db_connection()
    try:
        return create_profile_record(conn, user_id, profile)
    finally:
        conn.close()


def get_profile(profile_id: int, user_id: int) -> ProfileOut | None:
    conn = get_db_connection()
    try:
        return get_profile_record(conn, profile_id, user_id)
    finally:
        conn.close()


def get_profile_by_user_id(user_id: int) -> ProfileOut | None:
    conn = get_db_connection()
    try:
        return get_profile_by_user_id_record(conn, user_id)
    finally:
        conn.close()


def update_profile(
    profile_id: int,
    user_id: int,
    profile: ProfileIn,
) -> ProfileOut | None:
    conn = get_db_connection()
    try:
        return update_profile_record(conn, profile_id, user_id, profile)
    finally:
        conn.close()
