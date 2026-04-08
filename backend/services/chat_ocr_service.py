import json
from typing import Any
from urllib import error

from backend.config.estimate import get_estimate_ai_config
from backend.schemas.chat_ocr import (
    MAX_CHAT_OCR_IMAGE_BYTES,
    SUPPORTED_CHAT_OCR_CONTENT_TYPES,
    ChatOcrParseRequest,
    ChatOcrParseResponse,
    decode_chat_ocr_data_url,
)
from backend.services.ai_client import call_ai_with_image


DEFAULT_CHAT_OCR_FAILURE_REASON = "这张截图里没有稳定识别出商品主体，请重新上传，或改用文本输入。"
CHAT_OCR_CONFIRMATION_WARNING = "识别结果需要你确认后，才会继续进入点单决策。"
CHAT_OCR_RESPONSE_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "recognized_text": {"type": "string"},
        "primary_text": {"type": "string"},
        "confidence_level": {
            "type": "string",
            "enum": ["high", "medium", "low", "unknown"],
        },
        "candidate_titles": {
            "type": "array",
            "items": {"type": "string"},
        },
        "brand_candidate": {"type": "string"},
        "spec_candidate": {"type": "string"},
        "warnings": {
            "type": "array",
            "items": {"type": "string"},
        },
        "failure_reason": {"type": "string"},
    },
    "required": [
        "recognized_text",
        "primary_text",
        "confidence_level",
        "candidate_titles",
        "warnings",
        "failure_reason",
    ],
}

CHAT_OCR_SYSTEM_PROMPT = """
You are Food Pilot's OCR extraction layer for food ordering screenshots.
Reply in Simplified Chinese.

Task:
1. Read the screenshot and extract the main product text the user is likely asking about.
2. Ignore app chrome, delivery address, coupon slogans, activity banners, timestamps, and generic promotion text.
3. Prefer the main product or the clearest order item. If the screenshot is a noisy list, return the most likely primary item and lower confidence.
4. If there is no stable product subject, leave primary_text empty and explain why in failure_reason.
5. Return only JSON.

Field rules:
- recognized_text: concise OCR transcript of the useful food/product text only.
- primary_text: one editable text string the user can confirm and continue with.
- candidate_titles: up to 3 likely product title candidates.
- brand_candidate: brand/platform merchant name if visible.
- spec_candidate: visible size/spec/sugar/temperature/add-on text if stable.
- warnings: brief user-facing reminders about ambiguity or low confidence.
- failure_reason: empty string when primary_text is usable.
""".strip()

CHAT_OCR_USER_PROMPT = """
请识别这张点单或商品截图，提取最适合继续做“点单决策”的商品主体文本。
如果看不到明确商品主体，请返回空的 primary_text，并说明失败原因。
""".strip()


class ChatOcrServiceError(Exception):
    def __init__(
        self,
        *,
        status_code: int,
        message: str,
        user_message: str,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.message = message
        self.user_message = user_message


class MissingChatOcrConfigError(ChatOcrServiceError):
    def __init__(self) -> None:
        super().__init__(
            status_code=503,
            message="OCR AI config is missing",
            user_message="截图识别服务暂未配置，请稍后再试，或先改用文本输入。",
        )


class ChatOcrValidationError(ChatOcrServiceError):
    def __init__(self, user_message: str, *, message: str | None = None, status_code: int = 400) -> None:
        super().__init__(
            status_code=status_code,
            message=message or user_message,
            user_message=user_message,
        )


class ChatOcrUpstreamError(ChatOcrServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=503,
            message=message,
            user_message="截图识别服务暂时不可用，请稍后重试。",
        )


class ChatOcrInvalidResponseError(ChatOcrServiceError):
    def __init__(self, message: str) -> None:
        super().__init__(
            status_code=502,
            message=message,
            user_message="截图识别结果异常，请重新上传，或改用文本输入。",
        )


def parse_chat_screenshot(
    request: ChatOcrParseRequest,
    *,
    user_id: int | None = None,
) -> ChatOcrParseResponse:
    del user_id
    mime_type, image_bytes = _decode_and_validate_request(request)
    raw_response = _call_chat_ocr_ai(
        image_bytes=image_bytes,
        mime_type=mime_type,
        platform=request.platform,
        note=request.note,
    )
    return _build_chat_ocr_response(
        request,
        mime_type=mime_type,
        image_bytes=image_bytes,
        raw_response=raw_response,
    )


def _decode_and_validate_request(request: ChatOcrParseRequest) -> tuple[str, bytes]:
    try:
        mime_type, image_bytes = decode_chat_ocr_data_url(request.image_data_url)
    except ValueError as exc:
        raise ChatOcrValidationError("截图内容格式不正确，请重新上传。", message=str(exc)) from exc

    if mime_type not in SUPPORTED_CHAT_OCR_CONTENT_TYPES:
        raise ChatOcrValidationError("当前仅支持 PNG、JPEG 和 WebP 截图。")

    if request.content_type and request.content_type != mime_type:
        raise ChatOcrValidationError("截图格式校验失败，请重新选择图片。")

    if len(image_bytes) > MAX_CHAT_OCR_IMAGE_BYTES:
        raise ChatOcrValidationError("截图不能超过 5MB，请压缩后重试。", status_code=413)

    if request.file_size_bytes and abs(request.file_size_bytes - len(image_bytes)) > 16:
        raise ChatOcrValidationError("截图大小校验失败，请重新上传。")

    return mime_type, image_bytes


def _call_chat_ocr_ai(
    *,
    image_bytes: bytes,
    mime_type: str,
    platform: str | None,
    note: str | None,
) -> dict[str, Any]:
    config = get_estimate_ai_config()
    if not config.api_key:
        raise MissingChatOcrConfigError()

    user_prompt = CHAT_OCR_USER_PROMPT
    context_lines = []
    if platform:
        context_lines.append(f"平台提示: {platform}")
    if note:
        context_lines.append(f"用户补充说明: {note}")
    if context_lines:
        user_prompt = f"{user_prompt}\n\n" + "\n".join(context_lines)

    try:
        return call_ai_with_image(
            config,
            CHAT_OCR_SYSTEM_PROMPT,
            user_prompt,
            image_bytes=image_bytes,
            image_mime_type=mime_type,
            response_schema=CHAT_OCR_RESPONSE_SCHEMA,
        )
    except error.HTTPError as exc:
        exc.read()
        raise ChatOcrUpstreamError(f"OCR provider request failed ({exc.code}).") from exc
    except error.URLError as exc:
        raise ChatOcrUpstreamError("OCR provider is temporarily unavailable.") from exc
    except json.JSONDecodeError as exc:
        raise ChatOcrInvalidResponseError("OCR provider did not return valid JSON") from exc


def _build_chat_ocr_response(
    request: ChatOcrParseRequest,
    *,
    mime_type: str,
    image_bytes: bytes,
    raw_response: dict[str, Any],
) -> ChatOcrParseResponse:
    if not isinstance(raw_response, dict):
        raise ChatOcrInvalidResponseError("OCR response must be an object")

    recognized_text = _normalize_text(raw_response.get("recognized_text"))
    primary_text = _normalize_text(raw_response.get("primary_text"))
    candidate_titles = _normalize_string_list(raw_response.get("candidate_titles"))
    brand_candidate = _normalize_text(raw_response.get("brand_candidate"))
    spec_candidate = _normalize_text(raw_response.get("spec_candidate"))
    warnings = _normalize_string_list(raw_response.get("warnings"))
    failure_reason = _normalize_text(raw_response.get("failure_reason"))

    confidence_level = raw_response.get("confidence_level")
    if confidence_level not in {"high", "medium", "low", "unknown"}:
        confidence_level = "unknown"

    if not primary_text and candidate_titles:
        primary_text = candidate_titles[0]
    normalized_input = _normalize_text(primary_text)
    if not normalized_input:
        return ChatOcrParseResponse.model_validate(
            {
                "status": "failed",
                "recognized_text": recognized_text,
                "primary_text": None,
                "normalized_input": None,
                "confidence_level": "low" if confidence_level == "unknown" else confidence_level,
                "candidate_titles": candidate_titles,
                "brand_candidate": brand_candidate,
                "spec_candidate": spec_candidate,
                "warnings": warnings,
                "failure_reason": failure_reason or DEFAULT_CHAT_OCR_FAILURE_REASON,
                "file_name": request.file_name,
                "content_type": mime_type,
                "file_size_bytes": len(image_bytes),
                "platform": request.platform,
            }
        )

    response_warnings = [CHAT_OCR_CONFIRMATION_WARNING, *warnings]
    deduped_warnings = list(dict.fromkeys(response_warnings))
    return ChatOcrParseResponse.model_validate(
        {
            "status": "needs_confirmation",
            "recognized_text": recognized_text,
            "primary_text": primary_text,
            "normalized_input": normalized_input,
            "confidence_level": confidence_level,
            "candidate_titles": candidate_titles,
            "brand_candidate": brand_candidate,
            "spec_candidate": spec_candidate,
            "warnings": deduped_warnings,
            "failure_reason": None,
            "file_name": request.file_name,
            "content_type": mime_type,
            "file_size_bytes": len(image_bytes),
            "platform": request.platform,
        }
    )


def _normalize_text(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    normalized = " ".join(value.strip().split())
    return normalized or None


def _normalize_string_list(value: object) -> list[str]:
    if not isinstance(value, list):
        return []

    normalized_items: list[str] = []
    for item in value:
        normalized = _normalize_text(item)
        if normalized:
            normalized_items.append(normalized)
    return normalized_items[:3]
