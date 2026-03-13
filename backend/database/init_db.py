from backend.database.connection import get_db_connection


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    _ensure_users_table(cursor)
    _ensure_profiles_table(cursor)
    _ensure_chat_sessions_table(cursor)
    _ensure_messages_table(cursor)

    conn.commit()
    conn.close()


def _get_table_columns(cursor, table_name: str) -> set[str]:
    return {
        row[1]
        for row in cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    }


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

    profile_columns = _get_table_columns(cursor, "profiles")
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


def _ensure_chat_sessions_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            title TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            last_message_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deleted_at TEXT,
            CHECK (length(trim(title)) BETWEEN 1 AND 120)
        );
        """
    )
    chat_session_columns = _get_table_columns(cursor, "chat_sessions")
    if "last_message_at" not in chat_session_columns:
        cursor.execute(
            """
            ALTER TABLE chat_sessions
            ADD COLUMN last_message_at TEXT
            """
        )
        cursor.execute(
            """
            UPDATE chat_sessions
            SET last_message_at = COALESCE(updated_at, created_at, CURRENT_TIMESTAMP)
            WHERE last_message_at IS NULL
            """
        )

    if "deleted_at" not in chat_session_columns:
        cursor.execute(
            """
            ALTER TABLE chat_sessions
            ADD COLUMN deleted_at TEXT
            """
        )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_id
        ON chat_sessions(user_id);
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chat_sessions_last_message_at
        ON chat_sessions(last_message_at DESC, id DESC);
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_chat_sessions_user_last_message_at
        ON chat_sessions(user_id, last_message_at DESC, id DESC);
        """
    )
    cursor.execute(
        """
        CREATE TRIGGER IF NOT EXISTS chat_sessions_set_last_message_at_after_insert
        AFTER INSERT ON chat_sessions
        FOR EACH ROW
        WHEN NEW.last_message_at IS NULL
        BEGIN
            UPDATE chat_sessions
            SET last_message_at = COALESCE(NEW.created_at, CURRENT_TIMESTAMP)
            WHERE id = NEW.id;
        END;
        """
    )
    cursor.execute(
        """
        CREATE TRIGGER IF NOT EXISTS chat_sessions_set_updated_at
        AFTER UPDATE ON chat_sessions
        FOR EACH ROW
        WHEN NEW.updated_at = OLD.updated_at
        BEGIN
            UPDATE chat_sessions
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END;
        """
    )


def _ensure_messages_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS messages (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id INTEGER NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            role TEXT NOT NULL,
            message_type TEXT NOT NULL,
            content TEXT,
            result_title TEXT,
            result_confidence TEXT,
            result_description TEXT,
            result_items_json TEXT,
            result_total TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (role IN ('user', 'assistant')),
            CHECK (message_type IN ('text', 'estimate_result')),
            CHECK (content IS NULL OR length(trim(content)) > 0),
            CHECK (
                (
                    message_type = 'text'
                    AND result_title IS NULL
                    AND result_confidence IS NULL
                    AND result_description IS NULL
                    AND result_items_json IS NULL
                    AND result_total IS NULL
                    AND content IS NOT NULL
                )
                OR (
                    message_type = 'estimate_result'
                    AND role = 'assistant'
                    AND result_title IS NOT NULL
                    AND result_confidence IS NOT NULL
                    AND result_description IS NOT NULL
                    AND result_items_json IS NOT NULL
                    AND result_total IS NOT NULL
                    AND length(trim(result_title)) > 0
                    AND length(trim(result_confidence)) > 0
                    AND length(trim(result_description)) > 0
                    AND length(trim(result_items_json)) > 0
                    AND length(trim(result_total)) > 0
                )
            )
        );
        """
    )
    message_columns = _get_table_columns(cursor, "messages")
    if "user_id" not in message_columns:
        cursor.execute(
            """
            ALTER TABLE messages
            ADD COLUMN user_id INTEGER REFERENCES users(id) ON DELETE CASCADE
            """
        )
    if "message_type" not in message_columns:
        cursor.execute(
            """
            ALTER TABLE messages
            ADD COLUMN message_type TEXT
            """
        )
    if "result_title" not in message_columns:
        cursor.execute(
            """
            ALTER TABLE messages
            ADD COLUMN result_title TEXT
            """
        )
    if "result_confidence" not in message_columns:
        cursor.execute(
            """
            ALTER TABLE messages
            ADD COLUMN result_confidence TEXT
            """
        )
    if "result_description" not in message_columns:
        cursor.execute(
            """
            ALTER TABLE messages
            ADD COLUMN result_description TEXT
            """
        )
    if "result_items_json" not in message_columns:
        cursor.execute(
            """
            ALTER TABLE messages
            ADD COLUMN result_items_json TEXT
            """
        )
    if "result_total" not in message_columns:
        cursor.execute(
            """
            ALTER TABLE messages
            ADD COLUMN result_total TEXT
            """
        )

    cursor.execute(
        """
        UPDATE messages
        SET user_id = (
            SELECT user_id
            FROM chat_sessions
            WHERE chat_sessions.id = messages.session_id
        )
        WHERE user_id IS NULL
        """
    )
    cursor.execute(
        """
        UPDATE messages
        SET message_type = 'text'
        WHERE message_type IS NULL
        """
    )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_messages_session_id
        ON messages(session_id);
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_messages_user_id
        ON messages(user_id);
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_messages_session_id_id
        ON messages(session_id, id ASC);
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_messages_user_created_at
        ON messages(user_id, created_at DESC, id DESC);
        """
    )
    cursor.execute(
        """
        CREATE TRIGGER IF NOT EXISTS messages_touch_chat_session_after_insert
        AFTER INSERT ON messages
        FOR EACH ROW
        BEGIN
            UPDATE chat_sessions
            SET
                updated_at = CURRENT_TIMESTAMP,
                last_message_at = NEW.created_at
            WHERE id = NEW.session_id;
        END;
        """
    )


if __name__ == '__main__':
    init_db()
