from datetime import datetime, UTC

from backend.database.connection import get_db_connection


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    _ensure_users_table(cursor)
    _ensure_profiles_table(cursor)
    _ensure_chat_sessions_table(cursor)
    _ensure_messages_table(cursor)
    _ensure_food_log_entries_table(cursor)

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
    _create_messages_table(cursor)
    message_columns = _get_table_columns(cursor, "messages")
    if _requires_messages_rebuild(message_columns):
        _rebuild_messages_table(cursor, message_columns)
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


def _ensure_food_log_entries_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS food_log_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            source_type TEXT NOT NULL,
            session_id INTEGER REFERENCES chat_sessions(id) ON DELETE SET NULL,
            message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            confidence TEXT,
            description TEXT NOT NULL,
            items_json TEXT NOT NULL,
            total TEXT NOT NULL,
            suggestion TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (source_type IN ('estimate_api', 'chat_message')),
            CHECK (message_id IS NULL OR session_id IS NOT NULL),
            CHECK (length(trim(title)) > 0),
            CHECK (confidence IS NULL OR length(trim(confidence)) > 0),
            CHECK (length(trim(description)) > 0),
            CHECK (length(trim(items_json)) > 0),
            CHECK (length(trim(total)) > 0),
            CHECK (suggestion IS NULL OR length(trim(suggestion)) > 0)
        );
        """
    )
    food_log_columns = _get_table_columns(cursor, "food_log_entries")
    if "confidence" not in food_log_columns:
        cursor.execute(
            """
            ALTER TABLE food_log_entries
            ADD COLUMN confidence TEXT
            """
        )
    if "suggestion" not in food_log_columns:
        cursor.execute(
            """
            ALTER TABLE food_log_entries
            ADD COLUMN suggestion TEXT
            """
        )

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_food_log_entries_user_created_at
        ON food_log_entries(user_id, created_at DESC, id DESC);
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_food_log_entries_session_id
        ON food_log_entries(session_id);
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_food_log_entries_message_id_unique
        ON food_log_entries(message_id)
        WHERE message_id IS NOT NULL;
        """
    )

    _backfill_food_log_entries_from_messages(cursor)


def _create_messages_table(cursor, table_name: str = "messages") -> None:
    cursor.execute(
        f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
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


def _requires_messages_rebuild(message_columns: set[str]) -> bool:
    legacy_columns = {
        "time",
        "is_result",
        "title",
        "confidence",
        "description",
        "items_json",
        "total",
    }
    return any(column in message_columns for column in legacy_columns)


def _rebuild_messages_table(cursor, message_columns: set[str]) -> None:
    cursor.execute("DROP TABLE IF EXISTS messages__new")
    _create_messages_table(cursor, "messages__new")

    legacy_rows = cursor.execute("SELECT * FROM messages ORDER BY id ASC").fetchall()
    for row in legacy_rows:
        row_data = dict(row)
        requested_message_type = _resolve_message_type(row_data, message_columns)
        result_payload = _resolve_result_payload(row_data, message_columns, requested_message_type)
        message_type = "estimate_result" if result_payload is not None else "text"

        cursor.execute(
            """
            INSERT INTO messages__new (
                id,
                session_id,
                user_id,
                role,
                message_type,
                content,
                result_title,
                result_confidence,
                result_description,
                result_items_json,
                result_total,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row_data["id"],
                row_data["session_id"],
                _resolve_user_id(cursor, row_data, message_columns),
                row_data["role"],
                message_type,
                row_data.get("content"),
                result_payload["result_title"] if result_payload else None,
                result_payload["result_confidence"] if result_payload else None,
                result_payload["result_description"] if result_payload else None,
                result_payload["result_items_json"] if result_payload else None,
                result_payload["result_total"] if result_payload else None,
                _resolve_created_at_value(row_data, message_columns),
            ),
        )

    cursor.execute("DROP TABLE messages")
    cursor.execute("ALTER TABLE messages__new RENAME TO messages")


def _resolve_user_id(cursor, row_data: dict[str, object], message_columns: set[str]) -> int:
    user_id = row_data.get("user_id") if "user_id" in message_columns else None
    if user_id is not None:
        return int(user_id)

    session_row = cursor.execute(
        "SELECT user_id FROM chat_sessions WHERE id = ?",
        (row_data["session_id"],),
    ).fetchone()
    if session_row is None or session_row["user_id"] is None:
        raise ValueError("Cannot migrate message without owning user")
    return int(session_row["user_id"])


def _resolve_message_type(row_data: dict[str, object], message_columns: set[str]) -> str:
    message_type = row_data.get("message_type") if "message_type" in message_columns else None
    if isinstance(message_type, str) and message_type in {"text", "estimate_result"}:
        return message_type

    if "is_result" in message_columns and row_data.get("is_result"):
        return "estimate_result"
    return "text"


def _resolve_result_payload(
    row_data: dict[str, object],
    message_columns: set[str],
    message_type: str,
) -> dict[str, str | None] | None:
    result_title = _coalesce_row_value(row_data, message_columns, "result_title", "title")
    result_confidence = _coalesce_row_value(row_data, message_columns, "result_confidence", "confidence")
    result_description = _coalesce_row_value(row_data, message_columns, "result_description", "description")
    result_items_json = _coalesce_row_value(row_data, message_columns, "result_items_json", "items_json")
    result_total = _coalesce_row_value(row_data, message_columns, "result_total", "total")

    if message_type == "estimate_result" and all(
        _has_text(value)
        for value in (
            result_title,
            result_confidence,
            result_description,
            result_items_json,
            result_total,
        )
    ):
        return {
            "result_title": result_title,
            "result_confidence": result_confidence,
            "result_description": result_description,
            "result_items_json": result_items_json,
            "result_total": result_total,
        }

    return None


def _coalesce_row_value(
    row_data: dict[str, object],
    message_columns: set[str],
    *candidates: str,
) -> str | None:
    for candidate in candidates:
        if candidate in message_columns:
            value = row_data.get(candidate)
            if isinstance(value, str) and value.strip():
                return value
    return None


def _has_text(value: str | None) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _resolve_legacy_time_value(row_data: dict[str, object], message_columns: set[str]) -> str | None:
    if "time" not in message_columns:
        return None

    value = row_data.get("time")
    if isinstance(value, str) and value.strip():
        return value
    return None


def _resolve_created_at_value(row_data: dict[str, object], message_columns: set[str]) -> str:
    created_at = row_data.get("created_at")
    if isinstance(created_at, str) and created_at.strip():
        return created_at

    legacy_time = _resolve_legacy_time_value(row_data, message_columns)
    if legacy_time:
        return legacy_time

    return datetime.now(UTC).strftime("%Y-%m-%d %H:%M:%S")


def _backfill_food_log_entries_from_messages(cursor) -> None:
    cursor.execute(
        """
        INSERT INTO food_log_entries (
            user_id,
            source_type,
            session_id,
            message_id,
            title,
            confidence,
            description,
            items_json,
            total,
            suggestion,
            created_at
        )
        SELECT
            m.user_id,
            'chat_message',
            m.session_id,
            m.id,
            m.result_title,
            m.result_confidence,
            m.result_description,
            m.result_items_json,
            m.result_total,
            m.content,
            m.created_at
        FROM messages AS m
        WHERE m.message_type = 'estimate_result'
        AND NOT EXISTS (
            SELECT 1
            FROM food_log_entries AS f
            WHERE f.message_id = m.id
        )
        """
    )


if __name__ == '__main__':
    init_db()
