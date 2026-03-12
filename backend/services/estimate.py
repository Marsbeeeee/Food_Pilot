import json
from typing import Any
from urllib import error, parse, request

from backend.config.estimate import get_estimate_ai_config
from backend.schemas.estimate import EstimateResult
from backend.services.estimate_contract import (
    ESTIMATE_RESPONSE_INSTRUCTION,
    ESTIMATE_RESPONSE_SCHEMA,
)
from backend.services.estimate_parser import parse_estimate_payload


class EstimateServiceError(Exception):
    def __init__(
        self,
        *,
        code: str,
        status_code: int,
        message: str,
        retryable: bool,
    ) -> None:
        super().__init__(message)
        self.code = code
        self.status_code = status_code
        self.message = message
        self.retryable = retryable


class ProviderUnavailableError(EstimateServiceError):
    def __init__(self, message: str, *, retryable: bool) -> None:
        super().__init__(
            code="AI_PROVIDER_UNAVAILABLE",
            status_code=503,
            message=message,
            retryable=retryable,
        )


class InvalidAIResponseError(EstimateServiceError):
    def __init__(self, message: str = "AI returned an invalid response format") -> None:
        super().__init__(
            code="AI_RESPONSE_INVALID",
            status_code=502,
            message=message,
            retryable=True,
        )


def estimate_meal(query: str) -> EstimateResult:
    raw_response = _call_gemini_api(query)
    try:
        return parse_estimate_payload(raw_response)
    except ValueError as exc:
        raise InvalidAIResponseError(str(exc)) from exc


def _call_gemini_api(query: str) -> dict[str, Any]:
    config = get_estimate_ai_config()
    if not config.api_key:
        raise ProviderUnavailableError("AI provider is not configured. Set GEMINI_API_KEY.", retryable=False)

    endpoint = (
        f"https://generativelanguage.googleapis.com/v1beta/models/"
        f"{config.model}:generateContent?key={parse.quote(config.api_key)}"
    )

    payload = {
        "system_instruction": {
            "parts": [
                {
                    "text": (
                        f"{config.system_prompt}\n\n"
                        f"{ESTIMATE_RESPONSE_INSTRUCTION}"
                    )
                }
            ],
        },
        "contents": [
            {
                "role": "user",
                "parts": [{"text": query}],
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": ESTIMATE_RESPONSE_SCHEMA,
        },
    }
    body = json.dumps(payload).encode("utf-8")
    req = request.Request(
        endpoint,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with request.urlopen(req, timeout=config.timeout_seconds) as response:
            response_data = json.load(response)
    except error.HTTPError as exc:
        exc.read()
        if exc.code in {401, 403}:
            raise ProviderUnavailableError("AI provider authentication failed. Check GEMINI_API_KEY.", retryable=False) from exc
        raise ProviderUnavailableError(
            f"AI provider request failed ({exc.code}).",
            retryable=exc.code >= 500,
        ) from exc
    except error.URLError as exc:
        raise ProviderUnavailableError("AI provider is temporarily unavailable. Please try again later.", retryable=True) from exc

    try:
        text = response_data["candidates"][0]["content"]["parts"][0]["text"]
    except (KeyError, IndexError, TypeError) as exc:
        raise InvalidAIResponseError("AI provider did not return parseable content") from exc

    try:
        parsed = json.loads(text)
    except json.JSONDecodeError as exc:
        raise InvalidAIResponseError("AI provider did not return valid JSON") from exc

    if not isinstance(parsed, dict):
        raise InvalidAIResponseError("AI provider returned JSON that is not an object")
    return parsed
