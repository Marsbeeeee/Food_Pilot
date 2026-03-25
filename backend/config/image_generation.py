import os
from dataclasses import dataclass
from pathlib import Path


DEFAULT_STANDARD_DISH_IMAGE_PROMPT_VERSION = "v1"
DEFAULT_STANDARD_DISH_IMAGE_TIMEOUT_SECONDS = 45
DEFAULT_STANDARD_DISH_IMAGE_PROMPT_TEMPLATE = """
Generate a single high-quality food photo for the dish "{dish_name}".
Requirements:
- One clear dish as the only subject, centered in frame
- About a 45-degree slight top-down angle
- Clean off-white or light gray background
- Soft natural lighting
- Realistic, slightly idealized product-photo style
- No people, hands, or distracting utensils
- No text, watermark, logo, or collage
- Suitable for a clean product card cover image
Return only the generated image.
""".strip()


@dataclass(frozen=True)
class StandardDishImageGenerationConfig:
    enabled: bool
    api_key: str
    base_url: str
    model: str
    timeout_seconds: int
    prompt_version: str
    prompt_template: str
    mock_image_url: str


def get_standard_dish_image_generation_config() -> StandardDishImageGenerationConfig:
    api_key = _get_env_value("STANDARD_DISH_IMAGE_API_KEY")
    base_url = _get_env_value("STANDARD_DISH_IMAGE_BASE_URL")
    model = _get_env_value("STANDARD_DISH_IMAGE_MODEL")
    mock_image_url = _get_env_value("STANDARD_DISH_IMAGE_MOCK_URL")
    enabled_flag = _get_env_value("STANDARD_DISH_IMAGE_GENERATION_ENABLED").lower()
    enabled = enabled_flag in {"1", "true", "yes", "on"}
    if not enabled:
        enabled = bool(mock_image_url or (api_key and base_url and model))

    return StandardDishImageGenerationConfig(
        enabled=enabled,
        api_key=api_key,
        base_url=base_url,
        model=model,
        timeout_seconds=_get_timeout_seconds(),
        prompt_version=(
            _get_env_value("STANDARD_DISH_IMAGE_PROMPT_VERSION")
            or DEFAULT_STANDARD_DISH_IMAGE_PROMPT_VERSION
        ),
        prompt_template=(
            _get_env_value("STANDARD_DISH_IMAGE_PROMPT_TEMPLATE")
            or DEFAULT_STANDARD_DISH_IMAGE_PROMPT_TEMPLATE
        ),
        mock_image_url=mock_image_url,
    )


def _get_timeout_seconds() -> int:
    raw_timeout = _get_env_value("STANDARD_DISH_IMAGE_TIMEOUT_SECONDS")
    if not raw_timeout:
        return DEFAULT_STANDARD_DISH_IMAGE_TIMEOUT_SECONDS

    try:
        timeout_seconds = int(raw_timeout)
    except ValueError:
        return DEFAULT_STANDARD_DISH_IMAGE_TIMEOUT_SECONDS

    return (
        timeout_seconds
        if timeout_seconds > 0
        else DEFAULT_STANDARD_DISH_IMAGE_TIMEOUT_SECONDS
    )


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
