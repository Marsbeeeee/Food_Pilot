from backend.database.connection import get_db_connection


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    _ensure_users_table(cursor)
    _ensure_profiles_table(cursor)

    conn.commit()
    conn.close()


def _ensure_users_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT NOT NULL,
            password_hash TEXT NOT NULL,
            display_name TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email
        ON users(email);
        """
    )
    cursor.execute(
        """
        CREATE TRIGGER IF NOT EXISTS users_set_updated_at
        AFTER UPDATE ON users
        FOR EACH ROW
        WHEN NEW.updated_at = OLD.updated_at
        BEGIN
            UPDATE users
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END;
        """
    )


def _ensure_profiles_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER REFERENCES users(id) ON DELETE CASCADE,
            age INTEGER NOT NULL,
            height REAL NOT NULL,
            weight REAL NOT NULL,
            sex TEXT NOT NULL,
            activity_level TEXT NOT NULL,
            goal TEXT NOT NULL,
            kcal_target INTEGER NOT NULL,
            diet_style TEXT NOT NULL,
            allergies TEXT NOT NULL DEFAULT '[]',
            exercise_type TEXT NOT NULL,
            pace TEXT NOT NULL
        );
        """
    )

    profile_columns = {
        row[1]
        for row in cursor.execute("PRAGMA table_info(profiles)").fetchall()
    }
    if "user_id" not in profile_columns:
        cursor.execute(
            """
            ALTER TABLE profiles
            ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
            """
        )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_profiles_user_id
        ON profiles(user_id);
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_profiles_user_id_unique
        ON profiles(user_id)
        WHERE user_id IS NOT NULL;
        """
    )


if __name__ == '__main__':
    init_db()
