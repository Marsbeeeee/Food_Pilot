from backend.database.connection import get_db_connection
from backend.repositories.profile_repository import (
    create_profile as create_profile_record,
    get_profile as get_profile_record,
    update_profile as update_profile_record,
)
from backend.schemas.profile import ProfileIn, ProfileOut


def create_profile(profile: ProfileIn) -> ProfileOut:
    conn = get_db_connection()
    try:
        return create_profile_record(conn, profile)
    finally:
        conn.close()


def get_profile(profile_id: int) -> ProfileOut | None:
    conn = get_db_connection()
    try:
        return get_profile_record(conn, profile_id)
    finally:
        conn.close()


def update_profile(
    profile_id: int,
    profile: ProfileIn,
) -> ProfileOut | None:
    conn = get_db_connection()
    try:
        return update_profile_record(conn, profile_id, profile)
    finally:
        conn.close()
