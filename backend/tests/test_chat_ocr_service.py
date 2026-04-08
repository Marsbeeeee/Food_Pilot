import base64
import unittest
from unittest.mock import patch

from backend.config.estimate import EstimateAIConfig
from backend.schemas.chat_ocr import ChatOcrParseRequest
from backend.services.chat_ocr_service import (
    CHAT_OCR_CONFIRMATION_WARNING,
    parse_chat_screenshot,
)


def build_image_data_url(content_type: str = "image/png", payload: bytes = b"fake-png") -> str:
    encoded = base64.b64encode(payload).decode("ascii")
    return f"data:{content_type};base64,{encoded}"


class ChatOcrServiceTests(unittest.TestCase):
    def test_parse_chat_screenshot_returns_confirmation_payload(self) -> None:
        request = ChatOcrParseRequest.model_validate(
            {
                "imageDataUrl": build_image_data_url(),
                "fileName": "order.png",
                "contentType": "image/png",
                "fileSizeBytes": len(b"fake-png"),
                "platform": "美团",
            }
        )

        with patch(
            "backend.services.chat_ocr_service.get_estimate_ai_config",
            return_value=EstimateAIConfig(
                api_key="test-key",
                model="test-model",
                timeout_seconds=10,
                system_prompt="system",
            ),
        ), patch(
            "backend.services.chat_ocr_service.call_ai_with_image",
            return_value={
                "recognized_text": "霸王茶姬 伯牙绝弦 大杯 三分糖",
                "primary_text": "霸王茶姬 伯牙绝弦 大杯 三分糖",
                "confidence_level": "medium",
                "candidate_titles": ["霸王茶姬 伯牙绝弦 大杯 三分糖"],
                "brand_candidate": "霸王茶姬",
                "spec_candidate": "大杯 三分糖",
                "warnings": ["截图中还包含部分无关文案。"],
                "failure_reason": "",
            },
        ):
            response = parse_chat_screenshot(request, user_id=1)

        self.assertEqual(response.status, "needs_confirmation")
        self.assertEqual(response.normalized_input, "霸王茶姬 伯牙绝弦 大杯 三分糖")
        self.assertEqual(response.brand_candidate, "霸王茶姬")
        self.assertEqual(response.spec_candidate, "大杯 三分糖")
        self.assertIn(CHAT_OCR_CONFIRMATION_WARNING, response.warnings)

    def test_parse_chat_screenshot_returns_failed_payload_when_primary_text_missing(self) -> None:
        request = ChatOcrParseRequest.model_validate(
            {
                "imageDataUrl": build_image_data_url(),
                "fileName": "poster.png",
                "contentType": "image/png",
                "fileSizeBytes": len(b"fake-png"),
            }
        )

        with patch(
            "backend.services.chat_ocr_service.get_estimate_ai_config",
            return_value=EstimateAIConfig(
                api_key="test-key",
                model="test-model",
                timeout_seconds=10,
                system_prompt="system",
            ),
        ), patch(
            "backend.services.chat_ocr_service.call_ai_with_image",
            return_value={
                "recognized_text": "限时优惠 买一送一",
                "primary_text": "",
                "confidence_level": "low",
                "candidate_titles": [],
                "brand_candidate": "",
                "spec_candidate": "",
                "warnings": ["画面主体更像活动海报。"],
                "failure_reason": "这张图里没有稳定商品主体。",
            },
        ):
            response = parse_chat_screenshot(request)

        self.assertEqual(response.status, "failed")
        self.assertIsNone(response.normalized_input)
        self.assertEqual(response.failure_reason, "这张图里没有稳定商品主体。")

    def test_parse_chat_screenshot_rejects_unsupported_content_type(self) -> None:
        request = ChatOcrParseRequest.model_validate(
            {
                "imageDataUrl": build_image_data_url(content_type="image/gif"),
                "fileName": "order.gif",
                "contentType": "image/gif",
                "fileSizeBytes": len(b"fake-png"),
            }
        )

        with self.assertRaises(Exception) as exc:
            parse_chat_screenshot(request)

        self.assertIn("当前仅支持 PNG、JPEG 和 WebP 截图", str(exc.exception))


if __name__ == "__main__":
    unittest.main()
