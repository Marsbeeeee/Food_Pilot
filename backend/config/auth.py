from pathlib import Path
import os


def _get_env_value(*keys: str) -> str:
    project_root = Path(__file__).resolve().parents[2]
    candidate_files = [
        project_root / ".env",
        project_root / ".env.local",
        project_root / "frontend" / ".env.local",
    ]

    for key in keys:
        value = os.getenv(key)
        if value:
            return value.strip()
        for env_file in candidate_files:
            value = _read_env_file(env_file, key)
            if value:
                return value

    return ""


def _read_env_file(path: Path, key: str) -> str:
    if not path.exists():
        return ""

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        current_key, current_value = line.split("=", 1)
        if current_key.strip() != key:
            continue

        return current_value.strip().strip("'\"")

    return ""


def _get_env_int(key: str, default: int) -> int:
    raw_value = _get_env_value(key)
    if not raw_value:
        return default

    try:
        return int(raw_value)
    except ValueError:
        return default


AUTH_SECRET = _get_env_value("AUTH_SECRET") or "foodpilot-dev-secret"
AUTH_TOKEN_EXPIRE_SECONDS = _get_env_int("AUTH_TOKEN_EXPIRE_SECONDS", 604800)
PASSWORD_HASH_ITERATIONS = _get_env_int("PASSWORD_HASH_ITERATIONS", 120000)


def get_admin_emails() -> set[str]:
    raw_value = _get_env_value("ADMIN_EMAILS")
    return {
        email.strip().lower()
        for email in raw_value.split(",")
        if email.strip()
    }
