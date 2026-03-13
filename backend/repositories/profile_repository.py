import json
import sqlite3

from backend.schemas.profile import ProfileIn, ProfileOut


def create_profile(
    conn: sqlite3.Connection,
    user_id: int,
    profile: ProfileIn,
) -> ProfileOut:
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO profiles (
            user_id,
            age,
            height,
            weight,
            sex,
            activity_level,
            goal,
            kcal_target,
            diet_style,
            allergies,
            exercise_type,
            pace
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            profile.age,
            profile.height,
            profile.weight,
            profile.sex,
            profile.activity_level,
            profile.goal,
            profile.kcal_target,
            profile.diet_style,
            json.dumps(profile.allergies, ensure_ascii=False),
            profile.exercise_type,
            profile.pace,
        ),
    )
    conn.commit()
    return ProfileOut(id=cursor.lastrowid, **profile.model_dump())


def get_profile(
    conn: sqlite3.Connection,
    profile_id: int,
    user_id: int,
) -> ProfileOut | None:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id,
            age,
            height,
            weight,
            sex,
            activity_level,
            goal,
            kcal_target,
            diet_style,
            allergies,
            exercise_type,
            pace
        FROM profiles
        WHERE id = ? AND user_id = ?
        """,
        (profile_id, user_id),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return _row_to_profile(row)


def get_profile_by_user_id(
    conn: sqlite3.Connection,
    user_id: int,
) -> ProfileOut | None:
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT
            id,
            age,
            height,
            weight,
            sex,
            activity_level,
            goal,
            kcal_target,
            diet_style,
            allergies,
            exercise_type,
            pace
        FROM profiles
        WHERE user_id = ?
        """,
        (user_id,),
    )
    row = cursor.fetchone()
    if row is None:
        return None
    return _row_to_profile(row)


def update_profile(
    conn: sqlite3.Connection,
    profile_id: int,
    user_id: int,
    profile: ProfileIn,
) -> ProfileOut | None:
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE profiles
        SET
            age = ?,
            height = ?,
            weight = ?,
            sex = ?,
            activity_level = ?,
            goal = ?,
            kcal_target = ?,
            diet_style = ?,
            allergies = ?,
            exercise_type = ?,
            pace = ?
        WHERE id = ? AND user_id = ?
        """,
        (
            profile.age,
            profile.height,
            profile.weight,
            profile.sex,
            profile.activity_level,
            profile.goal,
            profile.kcal_target,
            profile.diet_style,
            json.dumps(profile.allergies, ensure_ascii=False),
            profile.exercise_type,
            profile.pace,
            profile_id,
            user_id,
        ),
    )
    conn.commit()
    if cursor.rowcount == 0:
        return None
    return ProfileOut(id=profile_id, **profile.model_dump())


def _row_to_profile(row: sqlite3.Row) -> ProfileOut:
    return ProfileOut.model_validate(dict(row))
