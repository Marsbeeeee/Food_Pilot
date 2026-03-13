import sqlite3

from backend.schemas.user import UserCreate, UserOut


def create_user(
    conn: sqlite3.Connection,
    user: UserCreate,
) -> UserOut:
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO users (
            email,
            password_hash,
            display_name
        ) VALUES (?, ?, ?)
        """,
        (
            user.email,
            user.password_hash,
            user.display_name,
        ),
    )
    conn.commit()
    return get_user_by_id(conn, cursor.lastrowid)


def get_user_by_id(
    conn: sqlite3.Connection,
    user_id: int,
) -> UserOut | None:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id,
            email,
            display_name,
            created_at,
            updated_at
        FROM users
        WHERE id = ?
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return UserOut.model_validate(dict(row))


def get_user_auth_by_email(
    conn: sqlite3.Connection,
    email: str,
) -> sqlite3.Row | None:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id,
            email,
            password_hash,
            display_name,
            created_at,
            updated_at
        FROM users
        WHERE email = ?
        """,
        (email,),
    )
    return cursor.fetchone()


def delete_user(
    conn: sqlite3.Connection,
    user_id: int,
) -> bool:
    cursor = conn.cursor()
    cursor.execute(
        """
        DELETE FROM users
        WHERE id = ?
        """,
        (user_id,),
    )
    conn.commit()
    return cursor.rowcount > 0
