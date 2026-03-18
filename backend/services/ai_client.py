"""
统一 AI 调用模块，支持 Gemini 与 OpenAI 兼容接口（如阿里云千问）。
"""
import json
from typing import Any
from urllib import error, parse, request

from backend.config.estimate import EstimateAIConfig


def call_ai(
    config: EstimateAIConfig,
    system_prompt: str,
    user_content: str,
    *,
    response_schema: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    调用 AI 接口，返回解析后的 JSON。
    根据 config.openai_base_url 自动选择 Gemini 或 OpenAI 兼容格式。
    - Gemini: 支持 response_schema 结构化输出
    - OpenAI 兼容（千问等）: 使用 response_format json_object，需在 prompt 中包含 JSON
    """
    if config.openai_base_url:
        return _call_openai_compatible(config, system_prompt, user_content)
    return _call_gemini(config, system_prompt, user_content, response_schema)


def _call_gemini(
    config: EstimateAIConfig,
    system_prompt: str,
    user_content: str,
    response_schema: dict[str, Any] | None,
) -> dict[str, Any]:
    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.model}:generateContent?key={parse.quote(config.api_key)}"
    )
    gen_config: dict[str, Any] = {"responseMimeType": "application/json"}
    if response_schema:
        gen_config["responseSchema"] = response_schema
    payload = {
        "system_instruction": {"parts": [{"text": system_prompt}]},
        "contents": [{"role": "user", "parts": [{"text": user_content}]}],
        "generationConfig": gen_config,
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with request.urlopen(req, timeout=config.timeout_seconds) as response:
        data = json.load(response)
    text = data["candidates"][0]["content"]["parts"][0]["text"]
    return json.loads(text)


def _call_openai_compatible(
    config: EstimateAIConfig,
    system_prompt: str,
    user_content: str,
) -> dict[str, Any]:
    """调用 OpenAI 兼容接口（阿里云千问等）。"""
    base = config.openai_base_url.rstrip("/")
    endpoint = f"{base}/chat/completions"
    payload = {
        "model": config.model,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_content},
        ],
        "response_format": {"type": "json_object"},
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        endpoint,
        data=body,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {config.api_key}",
        },
        method="POST",
    )
    with request.urlopen(req, timeout=config.timeout_seconds) as response:
        data = json.load(response)
    text = data["choices"][0]["message"]["content"]
    return json.loads(text)
