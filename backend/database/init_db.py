import json
from datetime import UTC, datetime

from backend.database.connection import get_db_connection
from backend.text import normalize_food_log_query


def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()

    _ensure_users_table(cursor)
    _ensure_profiles_table(cursor)
    _ensure_chat_sessions_table(cursor)
    _ensure_messages_table(cursor)
    _ensure_food_logs_table(cursor)
    _ensure_insights_analysis_table(cursor)
    _ensure_insights_basket_state_table(cursor)

    conn.commit()
    conn.close()


def _get_table_columns(cursor, table_name: str) -> set[str]:
    return {
        row[1]
        for row in cursor.execute(f"PRAGMA table_info({table_name})").fetchall()
    }


def _table_exists(cursor, table_name: str) -> bool:
    row = cursor.execute(
        """
        SELECT name
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (table_name,),
    ).fetchone()
    return row is not None


def _get_table_sql(cursor, table_name: str) -> str:
    row = cursor.execute(
        """
        SELECT sql
        FROM sqlite_master
        WHERE type = 'table' AND name = ?
        """,
        (table_name,),
    ).fetchone()
    if row is None or row["sql"] is None:
        return ""
    return str(row["sql"])


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
    message_table_sql = _get_table_sql(cursor, "messages")
    if _requires_messages_rebuild(message_columns, message_table_sql):
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
    if "payload_json" not in message_columns:
        cursor.execute(
            """
            ALTER TABLE messages
            ADD COLUMN payload_json TEXT
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
    _backfill_messages_payload_json(cursor)

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


def _ensure_food_logs_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS food_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            session_id INTEGER REFERENCES chat_sessions(id) ON DELETE SET NULL,
            source_message_id INTEGER REFERENCES messages(id) ON DELETE SET NULL,
            meal_description TEXT NOT NULL,
            normalized_query TEXT NOT NULL DEFAULT '',
            meal_occurred_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            logged_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            status TEXT NOT NULL DEFAULT 'active',
            result_title TEXT NOT NULL,
            result_confidence TEXT,
            result_description TEXT NOT NULL,
            total_calories TEXT NOT NULL,
            ingredients_json TEXT NOT NULL,
            source_type TEXT NOT NULL,
            is_manual INTEGER NOT NULL DEFAULT 0,
            idempotency_key TEXT,
            assistant_suggestion TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            deleted_at TEXT,
            CHECK (source_type IN ('estimate_api', 'chat_message', 'manual')),
            CHECK (status IN ('active', 'deleted')),
            CHECK (is_manual IN (0, 1)),
            CHECK (idempotency_key IS NULL OR length(trim(idempotency_key)) > 0),
            CHECK (source_message_id IS NULL OR session_id IS NOT NULL),
            CHECK (source_type = 'chat_message' OR source_message_id IS NULL),
            CHECK (length(trim(meal_description)) > 0),
            CHECK (length(trim(result_title)) > 0),
            CHECK (result_confidence IS NULL OR length(trim(result_confidence)) > 0),
            CHECK (length(trim(result_description)) > 0),
            CHECK (length(trim(total_calories)) > 0),
            CHECK (length(trim(ingredients_json)) > 0),
            CHECK (length(trim(source_type)) > 0),
            CHECK (assistant_suggestion IS NULL OR length(trim(assistant_suggestion)) > 0)
        );
        """
    )
    food_log_columns = _get_table_columns(cursor, "food_logs")
    if "result_confidence" not in food_log_columns:
        cursor.execute(
            """
            ALTER TABLE food_logs
            ADD COLUMN result_confidence TEXT
            """
        )
    if "assistant_suggestion" not in food_log_columns:
        cursor.execute(
            """
            ALTER TABLE food_logs
            ADD COLUMN assistant_suggestion TEXT
            """
        )
    if "normalized_query" not in food_log_columns:
        cursor.execute(
            """
            ALTER TABLE food_logs
            ADD COLUMN normalized_query TEXT
            """
        )
    if "meal_occurred_at" not in food_log_columns:
        cursor.execute(
            """
            ALTER TABLE food_logs
            ADD COLUMN meal_occurred_at TEXT
            """
        )
    if "status" not in food_log_columns:
        cursor.execute(
            """
            ALTER TABLE food_logs
            ADD COLUMN status TEXT
            """
        )
    if "updated_at" not in food_log_columns:
        cursor.execute(
            """
            ALTER TABLE food_logs
            ADD COLUMN updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            """
        )
    if "deleted_at" not in food_log_columns:
        cursor.execute(
            """
            ALTER TABLE food_logs
            ADD COLUMN deleted_at TEXT
            """
        )
    if "is_manual" not in food_log_columns:
        cursor.execute(
            """
            ALTER TABLE food_logs
            ADD COLUMN is_manual INTEGER
            """
        )
    if "idempotency_key" not in food_log_columns:
        cursor.execute(
            """
            ALTER TABLE food_logs
            ADD COLUMN idempotency_key TEXT
            """
        )
    if "image" not in food_log_columns:
        cursor.execute(
            """
            ALTER TABLE food_logs
            ADD COLUMN image TEXT
            """
        )
    if "image_source" not in food_log_columns:
        cursor.execute(
            """
            ALTER TABLE food_logs
            ADD COLUMN image_source TEXT
            """
        )
    if "image_license" not in food_log_columns:
        cursor.execute(
            """
            ALTER TABLE food_logs
            ADD COLUMN image_license TEXT
            """
        )

    cursor.execute(
        """
        DROP INDEX IF EXISTS idx_food_logs_user_normalized_query_unique
        """
    )
    _migrate_legacy_food_log_entries(cursor)
    _backfill_food_log_normalized_queries(cursor)
    _backfill_food_log_meal_occurred_at(cursor)
    _backfill_food_log_status(cursor)
    _backfill_food_log_is_manual(cursor)
    _backfill_food_log_idempotency_keys(cursor)

    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_food_logs_user_id
        ON food_logs(user_id);
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_food_logs_user_logged_at
        ON food_logs(user_id, logged_at DESC, id DESC);
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_food_logs_user_meal_occurred_at
        ON food_logs(user_id, meal_occurred_at DESC, id DESC);
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_food_logs_user_updated_at
        ON food_logs(user_id, updated_at DESC, id DESC);
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_food_logs_session_id
        ON food_logs(session_id);
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_food_logs_logged_at
        ON food_logs(logged_at DESC, id DESC);
        """
    )
    cursor.execute(
        """
        DROP INDEX IF EXISTS idx_food_logs_source_message_id_unique
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_food_logs_source_message_id
        ON food_logs(source_message_id)
        WHERE source_message_id IS NOT NULL;
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_food_logs_user_idempotency_key_unique
        ON food_logs(user_id, idempotency_key)
        WHERE idempotency_key IS NOT NULL AND trim(idempotency_key) != '';
        """
    )
    cursor.execute(
        """
        CREATE TRIGGER IF NOT EXISTS food_logs_set_updated_at
        AFTER UPDATE ON food_logs
        FOR EACH ROW
        WHEN NEW.updated_at = OLD.updated_at
        BEGIN
            UPDATE food_logs
            SET updated_at = CURRENT_TIMESTAMP
            WHERE id = NEW.id;
        END;
        """
    )


def _ensure_insights_analysis_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS insights_analysis (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            cache_key TEXT NOT NULL,
            mode TEXT NOT NULL,
            date_start TEXT NOT NULL,
            date_end TEXT NOT NULL,
            selected_log_ids_json TEXT NOT NULL,
            result_json TEXT NOT NULL,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (mode IN ('day', 'week')),
            CHECK (length(trim(cache_key)) > 0)
        );
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_insights_analysis_user_id
        ON insights_analysis(user_id);
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_insights_analysis_user_created_at
        ON insights_analysis(user_id, created_at DESC, id DESC);
        """
    )
    cursor.execute(
        """
        DROP INDEX IF EXISTS idx_insights_analysis_user_cache_key
        """
    )
    cursor.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_insights_analysis_user_cache_key
        ON insights_analysis(user_id, cache_key);
        """
    )
    _dedupe_insights_analysis_rows(cursor)
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_insights_analysis_user_mode_range
        ON insights_analysis(user_id, mode, date_start, date_end);
        """
    )


def _dedupe_insights_analysis_rows(cursor) -> None:
    """Keep only the latest row for each user+mode+date_start+date_end group."""
    cursor.execute(
        """
        DELETE FROM insights_analysis
        WHERE id IN (
            SELECT older.id
            FROM insights_analysis AS older
            JOIN insights_analysis AS newer
              ON newer.user_id = older.user_id
             AND newer.mode = older.mode
             AND newer.date_start = older.date_start
             AND newer.date_end = older.date_end
             AND (
                 newer.created_at > older.created_at
                 OR (
                     newer.created_at = older.created_at
                     AND newer.id > older.id
                 )
             )
        )
        """
    )


def _ensure_insights_basket_state_table(cursor) -> None:
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS insights_basket_state (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
            basket_json TEXT NOT NULL DEFAULT '[]',
            updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (length(trim(basket_json)) > 0)
        );
        """
    )
    cursor.execute(
        """
        CREATE UNIQUE INDEX IF NOT EXISTS idx_insights_basket_state_user_id
        ON insights_basket_state(user_id);
        """
    )


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
            payload_json TEXT,
            result_title TEXT,
            result_confidence TEXT,
            result_description TEXT,
            result_items_json TEXT,
            result_total TEXT,
            created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CHECK (role IN ('user', 'assistant')),
            CHECK (
                CASE
                    WHEN message_type = 'estimate_result' THEN 'meal_estimate'
                    ELSE message_type
                END IN ('text', 'meal_estimate', 'meal_recommendation')
            ),
            CHECK (content IS NULL OR length(trim(content)) > 0),
            CHECK (payload_json IS NULL OR length(trim(payload_json)) > 0),
            CHECK (result_title IS NULL OR length(trim(result_title)) > 0),
            CHECK (result_confidence IS NULL OR length(trim(result_confidence)) > 0),
            CHECK (result_description IS NULL OR length(trim(result_description)) > 0),
            CHECK (result_items_json IS NULL OR length(trim(result_items_json)) > 0),
            CHECK (result_total IS NULL OR length(trim(result_total)) > 0),
            CHECK (
                (
                    CASE
                        WHEN message_type = 'estimate_result' THEN 'meal_estimate'
                        ELSE message_type
                    END = 'text'
                    AND content IS NOT NULL
                )
                OR (
                    CASE
                        WHEN message_type = 'estimate_result' THEN 'meal_estimate'
                        ELSE message_type
                    END IN ('meal_estimate', 'meal_recommendation')
                    AND role = 'assistant'
                    AND (
                        payload_json IS NOT NULL
                        OR (
                            message_type = 'estimate_result'
                            AND result_title IS NOT NULL
                            AND result_confidence IS NOT NULL
                            AND result_description IS NOT NULL
                            AND result_items_json IS NOT NULL
                            AND result_total IS NOT NULL
                        )
                    )
                )
            )
        );
        """
    )


def _requires_messages_rebuild(message_columns: set[str], table_sql: str) -> bool:
    legacy_columns = {
        "time",
        "is_result",
        "title",
        "confidence",
        "description",
        "items_json",
        "total",
    }
    if any(column in message_columns for column in legacy_columns):
        return True
    if "payload_json" not in message_columns:
        return True

    normalized_sql = table_sql.lower()
    return any(
        marker not in normalized_sql
        for marker in ("payload_json", "meal_estimate", "meal_recommendation")
    )


def _rebuild_messages_table(cursor, message_columns: set[str]) -> None:
    cursor.execute("DROP TABLE IF EXISTS messages__new")
    _create_messages_table(cursor, "messages__new")

    legacy_rows = cursor.execute("SELECT * FROM messages ORDER BY id ASC").fetchall()
    for row in legacy_rows:
        row_data = dict(row)
        message_type = _resolve_message_type(row_data, message_columns)
        result_payload = _resolve_result_payload(row_data, message_columns, message_type)
        payload_json = _resolve_payload_json(
            row_data,
            message_columns,
            message_type,
            result_payload,
        )

        cursor.execute(
            """
            INSERT INTO messages__new (
                id,
                session_id,
                user_id,
                role,
                message_type,
                content,
                payload_json,
                result_title,
                result_confidence,
                result_description,
                result_items_json,
                result_total,
                created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                row_data["id"],
                row_data["session_id"],
                _resolve_user_id(cursor, row_data, message_columns),
                row_data["role"],
                message_type,
                row_data.get("content"),
                payload_json,
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
    if isinstance(message_type, str) and message_type in {
        "text",
        "estimate_result",
        "meal_estimate",
        "meal_recommendation",
    }:
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

    if message_type in {"estimate_result", "meal_estimate"} and all(
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


def _backfill_messages_payload_json(cursor) -> None:
    rows = cursor.execute(
        """
        SELECT
            id,
            message_type,
            content,
            payload_json,
            result_title,
            result_confidence,
            result_description,
            result_items_json,
            result_total
        FROM messages
        WHERE payload_json IS NULL OR trim(payload_json) = ''
        ORDER BY id ASC
        """
    ).fetchall()
    message_columns = _get_table_columns(cursor, "messages")

    for row in rows:
        row_data = dict(row)
        message_type = _resolve_message_type(row_data, message_columns)
        result_payload = _resolve_result_payload(row_data, message_columns, message_type)
        payload_json = _resolve_payload_json(
            row_data,
            message_columns,
            message_type,
            result_payload,
        )
        if payload_json is None:
            continue

        cursor.execute(
            """
            UPDATE messages
            SET payload_json = ?
            WHERE id = ?
            """,
            (payload_json, int(row["id"])),
        )


def _resolve_payload_json(
    row_data: dict[str, object],
    message_columns: set[str],
    message_type: str,
    result_payload: dict[str, str | None] | None,
) -> str | None:
    if "payload_json" in message_columns:
        existing_payload_json = row_data.get("payload_json")
        if isinstance(existing_payload_json, str) and existing_payload_json.strip():
            return existing_payload_json

    if message_type == "text":
        content = _coalesce_row_value(row_data, message_columns, "content")
        if _has_text(content):
            return json.dumps({"text": content}, ensure_ascii=False)
        return None

    if message_type in {"estimate_result", "meal_estimate"}:
        payload: dict[str, object] = {}
        if result_payload is not None:
            payload["title"] = result_payload["result_title"]
            payload["confidence"] = result_payload["result_confidence"]
            payload["description"] = result_payload["result_description"]
            payload["total"] = result_payload["result_total"]

            items = _parse_json_list(result_payload["result_items_json"])
            if items is not None:
                payload["items"] = items
        elif message_type == "estimate_result":
            return None

        if payload:
            return json.dumps(payload, ensure_ascii=False)

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


def _parse_json_list(value: str | None) -> list[object] | None:
    if not _has_text(value):
        return None

    try:
        parsed = json.loads(value)
    except json.JSONDecodeError:
        return None

    if not isinstance(parsed, list):
        return None
    return parsed


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


def _migrate_legacy_food_log_entries(cursor) -> None:
    if not _table_exists(cursor, "food_log_entries"):
        return

    cursor.execute(
        """
        INSERT INTO food_logs (
            user_id,
            session_id,
            source_message_id,
            meal_description,
            meal_occurred_at,
            logged_at,
            status,
            result_title,
            result_confidence,
            result_description,
            total_calories,
            ingredients_json,
            source_type,
            is_manual,
            idempotency_key,
            assistant_suggestion,
            created_at,
            updated_at
        )
        SELECT
            legacy.user_id,
            legacy.session_id,
            legacy.message_id,
            COALESCE(
                (
                    SELECT user_message.content
                    FROM messages AS user_message
                    WHERE user_message.session_id = legacy.session_id
                    AND user_message.role = 'user'
                    AND legacy.message_id IS NOT NULL
                    AND user_message.id < legacy.message_id
                    ORDER BY user_message.id DESC
                    LIMIT 1
                ),
                legacy.suggestion,
                legacy.title
            ),
            COALESCE(legacy.created_at, CURRENT_TIMESTAMP),
            COALESCE(legacy.created_at, CURRENT_TIMESTAMP),
            'active',
            legacy.title,
            legacy.confidence,
            legacy.description,
            legacy.total,
            legacy.items_json,
            legacy.source_type,
            CASE WHEN legacy.source_type = 'manual' THEN 1 ELSE 0 END,
            CASE
                WHEN legacy.message_id IS NOT NULL THEN 'chat_message:' || legacy.message_id
                ELSE NULL
            END,
            legacy.suggestion,
            COALESCE(legacy.created_at, CURRENT_TIMESTAMP),
            COALESCE(legacy.created_at, CURRENT_TIMESTAMP)
        FROM food_log_entries AS legacy
        WHERE NOT EXISTS (
            SELECT 1
            FROM food_logs AS current_logs
            WHERE current_logs.source_message_id = legacy.message_id
            AND legacy.message_id IS NOT NULL
        )
        AND (
            legacy.message_id IS NOT NULL
            OR NOT EXISTS (
                SELECT 1
                FROM food_logs AS current_logs
                WHERE current_logs.user_id = legacy.user_id
                AND current_logs.source_message_id IS NULL
                AND current_logs.logged_at = COALESCE(legacy.created_at, CURRENT_TIMESTAMP)
                AND current_logs.result_title = legacy.title
            )
        )
        """
    )


def _backfill_food_log_normalized_queries(cursor) -> None:
    rows = cursor.execute(
        """
        SELECT id, meal_description
        FROM food_logs
        """
    ).fetchall()
    for row in rows:
        cursor.execute(
            """
            UPDATE food_logs
            SET normalized_query = ?
            WHERE id = ?
            """,
            (normalize_food_log_query(str(row["meal_description"])), row["id"]),
        )


def _backfill_food_log_meal_occurred_at(cursor) -> None:
    cursor.execute(
        """
        UPDATE food_logs
        SET meal_occurred_at = COALESCE(
            meal_occurred_at,
            logged_at,
            created_at,
            updated_at,
            CURRENT_TIMESTAMP
        )
        WHERE meal_occurred_at IS NULL OR trim(meal_occurred_at) = ''
        """
    )


def _backfill_food_log_status(cursor) -> None:
    cursor.execute(
        """
        UPDATE food_logs
        SET status = CASE
            WHEN deleted_at IS NOT NULL THEN 'deleted'
            ELSE 'active'
        END
        WHERE status IS NULL OR trim(status) = ''
        """
    )
    cursor.execute(
        """
        UPDATE food_logs
        SET status = 'deleted'
        WHERE deleted_at IS NOT NULL AND status != 'deleted'
        """
    )


def _backfill_food_log_is_manual(cursor) -> None:
    cursor.execute(
        """
        UPDATE food_logs
        SET is_manual = CASE
            WHEN source_type = 'manual' THEN 1
            ELSE 0
        END
        WHERE is_manual IS NULL
        """
    )


def _backfill_food_log_idempotency_keys(cursor) -> None:
    rows = cursor.execute(
        """
        SELECT id, user_id, source_type, source_message_id, idempotency_key
        FROM food_logs
        """
    ).fetchall()
    source_message_counts: dict[tuple[int, int], int] = {}
    for row in rows:
        source_message_id = row["source_message_id"]
        if source_message_id is None:
            continue
        key = (int(row["user_id"]), int(source_message_id))
        source_message_counts[key] = source_message_counts.get(key, 0) + 1

    for row in rows:
        current_key = row["idempotency_key"]
        if isinstance(current_key, str) and current_key.strip():
            continue
        if row["source_type"] != "chat_message" or row["source_message_id"] is None:
            continue
        source_message_id = int(row["source_message_id"])
        key = (int(row["user_id"]), source_message_id)
        if source_message_counts.get(key, 0) != 1:
            continue
        cursor.execute(
            """
            UPDATE food_logs
            SET idempotency_key = ?
            WHERE id = ?
            """,
            (f"chat_message:{source_message_id}", int(row["id"])),
        )


if __name__ == '__main__':
    init_db()
