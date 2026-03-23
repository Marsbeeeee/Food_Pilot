import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_FOOD_KB_ENABLED = True
DEFAULT_FOOD_KB_TOP_K = 3
DEFAULT_FOOD_KB_MIN_SCORE = 1.35
DEFAULT_FOOD_KB_MAX_CONTEXT_CHARS = 1200
DEFAULT_FOOD_KB_ONLY_CHINESE = True


@dataclass(frozen=True)
class FoodKnowledgeConfig:
    enabled: bool
    data_path: Path
    top_k: int
    min_score: float
    max_context_chars: int
    only_chinese: bool


def get_food_knowledge_config() -> FoodKnowledgeConfig:
    data_path = _resolve_data_path(
        _get_env_value("FOOD_KB_DATA_PATH")
        or str(Path(__file__).resolve().parents[1] / "data" / "chinese_food_kb_seed.json")
    )

    return FoodKnowledgeConfig(
        enabled=_get_env_bool("FOOD_KB_ENABLED", DEFAULT_FOOD_KB_ENABLED),
        data_path=data_path,
        top_k=_get_env_int("FOOD_KB_TOP_K", DEFAULT_FOOD_KB_TOP_K, minimum=1, maximum=8),
        min_score=_get_env_float("FOOD_KB_MIN_SCORE", DEFAULT_FOOD_KB_MIN_SCORE, minimum=0.1, maximum=20.0),
        max_context_chars=_get_env_int(
            "FOOD_KB_MAX_CONTEXT_CHARS",
            DEFAULT_FOOD_KB_MAX_CONTEXT_CHARS,
            minimum=200,
            maximum=4000,
        ),
        only_chinese=_get_env_bool("FOOD_KB_ONLY_CHINESE", DEFAULT_FOOD_KB_ONLY_CHINESE),
    )


def _resolve_data_path(raw_value: str) -> Path:
    candidate = Path(raw_value)
    if candidate.is_absolute():
        return candidate
    return (Path(__file__).resolve().parents[2] / candidate).resolve()


def _get_env_bool(key: str, default: bool) -> bool:
    raw = _get_env_value(key)
    if not raw:
        return default
    normalized = raw.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    return default


def _get_env_int(
    key: str,
    default: int,
    *,
    minimum: int | None = None,
    maximum: int | None = None,
) -> int:
    raw = _get_env_value(key)
    if not raw:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    if minimum is not None and value < minimum:
        return default
    if maximum is not None and value > maximum:
        return default
    return value


def _get_env_float(
    key: str,
    default: float,
    *,
    minimum: float | None = None,
    maximum: float | None = None,
) -> float:
    raw = _get_env_value(key)
    if not raw:
        return default
    try:
        value = float(raw)
    except ValueError:
        return default
    if minimum is not None and value < minimum:
        return default
    if maximum is not None and value > maximum:
        return default
    return value


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
