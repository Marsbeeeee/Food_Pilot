import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_MODEL = "gemini-3-flash-preview"
DEFAULT_OPENAI_MODEL = "qwen-plus"
DEFAULT_TIMEOUT_SECONDS = 20
DEFAULT_SYSTEM_PROMPT = """
You are Food Pilot, a friendly and professional nutrition assistant.
Reply in Simplified Chinese.
Estimate calories conservatively, break down the meal into ingredients,
handle common Chinese dishes and mixed meals naturally,
and provide a short practical suggestion.
Return only JSON that matches the requested schema.
""".strip()

# 阿里云千问 OpenAI 兼容接口 base URL
QWEN_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


@dataclass(frozen=True)
class EstimateAIConfig:
    api_key: str
    model: str
    timeout_seconds: int
    system_prompt: str
    # 若设置，则使用 OpenAI 兼容接口（如阿里云千问）
    openai_base_url: str = ""


def get_estimate_ai_config() -> EstimateAIConfig:
    # 优先使用 DASHSCOPE_API_KEY（千问），其次 GEMINI_API_KEY / API_KEY
    api_key = (
        _get_env_value("DASHSCOPE_API_KEY")
        or _get_env_value("GEMINI_API_KEY", "API_KEY")
    )
    base_url = _get_env_value("AI_BASE_URL", "DASHSCOPE_BASE_URL") or ""
    # 若设置了 DASHSCOPE_API_KEY 但未设置 base_url，默认使用千问
    if api_key and not base_url and _get_env_value("DASHSCOPE_API_KEY"):
        base_url = QWEN_BASE_URL
    model_key = "AI_MODEL" if base_url else "GEMINI_MODEL"
    default_model = DEFAULT_OPENAI_MODEL if base_url else DEFAULT_MODEL
    model = _get_env_value(model_key, "GEMINI_MODEL") or default_model

    return EstimateAIConfig(
        api_key=api_key,
        model=model,
        timeout_seconds=_get_timeout_seconds(),
        system_prompt=_get_env_value("GEMINI_SYSTEM_PROMPT") or DEFAULT_SYSTEM_PROMPT,
        openai_base_url=base_url,
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
