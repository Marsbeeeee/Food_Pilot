import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_MODEL = "gemini-3-flash-preview"
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_SYSTEM_PROMPT = """
You are Food Pilot, a friendly and professional nutrition assistant.
Reply in Simplified Chinese.
Estimate calories conservatively, break down the meal into ingredients,
and provide a short practical suggestion.
Return only JSON that matches the requested schema.
""".strip()


@dataclass(frozen=True)
class EstimateAIConfig:
    api_key: str
    model: str
    timeout_seconds: int
    system_prompt: str


def get_estimate_ai_config() -> EstimateAIConfig:
    return EstimateAIConfig(
        api_key=_get_env_value("GEMINI_API_KEY", "API_KEY"),
        model=_get_env_value("GEMINI_MODEL") or DEFAULT_MODEL,
        timeout_seconds=_get_timeout_seconds(),
        system_prompt=_get_env_value("GEMINI_SYSTEM_PROMPT") or DEFAULT_SYSTEM_PROMPT,
    )


def _get_timeout_seconds() -> int:
    raw_timeout = _get_env_value("GEMINI_TIMEOUT_SECONDS")
    if not raw_timeout:
        return DEFAULT_TIMEOUT_SECONDS

    try:
        timeout_seconds = int(raw_timeout)
    except ValueError:
        return DEFAULT_TIMEOUT_SECONDS

    return timeout_seconds if timeout_seconds > 0 else DEFAULT_TIMEOUT_SECONDS


def _get_env_value(*keys: str) -> str:
    for key in keys:
        value = os.getenv(key)
        if value:
            return value.strip()

    project_root = Path(__file__).resolve().parents[2]
    candidate_files = [
        project_root / ".env",
        project_root / ".env.local",
        project_root / "frontend" / ".env.local",
    ]

    for env_file in candidate_files:
        for key in keys:
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
