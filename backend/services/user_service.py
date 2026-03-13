import sqlite3

from backend.database.connection import get_db_connection
from backend.repositories.user_repository import (
    create_user as create_user_record,
    get_user_auth_by_email as get_user_auth_by_email_record,
    get_user_by_id as get_user_by_id_record,
)
from backend.schemas.user import UserCreate, UserOut


def create_user(user: UserCreate) -> UserOut:
    conn = get_db_connection()
    try:
        return create_user_record(conn, user)
    finally:
        conn.close()


def get_user_by_id(user_id: int) -> UserOut | None:
    conn = get_db_connection()
    try:
        return get_user_by_id_record(conn, user_id)
    finally:
        conn.close()


def get_user_auth_by_email(email: str) -> sqlite3.Row | None:
    conn = get_db_connection()
    try:
        return get_user_auth_by_email_record(conn, email)
    finally:
        conn.close()
