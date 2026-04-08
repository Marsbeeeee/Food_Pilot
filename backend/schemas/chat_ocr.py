import base64
import math
import re
from typing import Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, field_validator


SUPPORTED_CHAT_OCR_CONTENT_TYPES = (
    "image/png",
    "image/jpeg",
    "image/webp",
)
MAX_CHAT_OCR_IMAGE_BYTES = 5 * 1024 * 1024
DATA_URL_PATTERN = re.compile(r"^data:(?P<mime>[\w./+-]+);base64,(?P<data>.+)$")

ChatOcrStatus = Literal["needs_confirmation", "failed"]
ChatOcrConfidenceLevel = Literal["high", "medium", "low", "unknown"]


class ChatOcrParseRequest(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    image_data_url: str = Field(
        validation_alias=AliasChoices("image_data_url", "imageDataUrl"),
        serialization_alias="imageDataUrl",
    )
    file_name: str = Field(
        validation_alias=AliasChoices("file_name", "fileName"),
        serialization_alias="fileName",
    )
    content_type: str | None = Field(
        default=None,
        validation_alias=AliasChoices("content_type", "contentType"),
        serialization_alias="contentType",
    )
    file_size_bytes: int | None = Field(
        default=None,
        validation_alias=AliasChoices("file_size_bytes", "fileSizeBytes"),
        serialization_alias="fileSizeBytes",
    )
    platform: str | None = None
    note: str | None = None

    @field_validator("image_data_url")
    @classmethod
    def validate_image_data_url(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("image_data_url is required")
        if not DATA_URL_PATTERN.match(normalized):
            raise ValueError("image_data_url must be a base64 data URL")
        return normalized

    @field_validator("file_name")
    @classmethod
    def validate_file_name(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("file_name is required")
        if len(normalized) > 200:
            raise ValueError("file_name must be 200 characters or fewer")
        return normalized

    @field_validator("content_type")
    @classmethod
    def validate_content_type(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = value.strip().lower()
        if not normalized:
            return None
        return normalized

    @field_validator("file_size_bytes")
    @classmethod
    def validate_file_size_bytes(cls, value: int | None) -> int | None:
        if value is None:
            return None
        if value <= 0:
            raise ValueError("file_size_bytes must be greater than 0")
        return value

    @field_validator("platform", "note")
    @classmethod
    def validate_optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalized = " ".join(value.strip().split())
        return normalized or None


class ChatOcrParseResponse(BaseModel):
    model_config = ConfigDict(extra="forbid", populate_by_name=True)

    status: ChatOcrStatus
    recognized_text: str | None = Field(
        default=None,
        validation_alias=AliasChoices("recognized_text", "recognizedText"),
        serialization_alias="recognizedText",
    )
    primary_text: str | None = Field(
        default=None,
        validation_alias=AliasChoices("primary_text", "primaryText"),
        serialization_alias="primaryText",
    )
    normalized_input: str | None = Field(
        default=None,
        validation_alias=AliasChoices("normalized_input", "normalizedInput"),
        serialization_alias="normalizedInput",
    )
    confidence_level: ChatOcrConfidenceLevel = Field(
        default="unknown",
        validation_alias=AliasChoices("confidence_level", "confidenceLevel"),
        serialization_alias="confidenceLevel",
    )
    candidate_titles: list[str] = Field(
        default_factory=list,
        validation_alias=AliasChoices("candidate_titles", "candidateTitles"),
        serialization_alias="candidateTitles",
    )
    brand_candidate: str | None = Field(
        default=None,
        validation_alias=AliasChoices("brand_candidate", "brandCandidate"),
        serialization_alias="brandCandidate",
    )
    spec_candidate: str | None = Field(
        default=None,
        validation_alias=AliasChoices("spec_candidate", "specCandidate"),
        serialization_alias="specCandidate",
    )
    warnings: list[str] = Field(default_factory=list)
    failure_reason: str | None = Field(
        default=None,
        validation_alias=AliasChoices("failure_reason", "failureReason"),
        serialization_alias="failureReason",
    )
    file_name: str = Field(
        validation_alias=AliasChoices("file_name", "fileName"),
        serialization_alias="fileName",
    )
    content_type: str = Field(
        validation_alias=AliasChoices("content_type", "contentType"),
        serialization_alias="contentType",
    )
    file_size_bytes: int = Field(
        validation_alias=AliasChoices("file_size_bytes", "fileSizeBytes"),
        serialization_alias="fileSizeBytes",
    )
    platform: str | None = None


def decode_chat_ocr_data_url(data_url: str) -> tuple[str, bytes]:
    match = DATA_URL_PATTERN.match(data_url.strip())
    if not match:
        raise ValueError("image_data_url must be a base64 data URL")

    mime_type = match.group("mime").strip().lower()
    try:
        image_bytes = base64.b64decode(match.group("data"), validate=True)
    except (ValueError, base64.binascii.Error) as exc:
        raise ValueError("image_data_url is not valid base64") from exc

    if not image_bytes:
        raise ValueError("image_data_url decoded to empty content")

    return mime_type, image_bytes


def estimate_chat_ocr_image_bytes(data_url: str) -> int:
    match = DATA_URL_PATTERN.match(data_url.strip())
    if not match:
        raise ValueError("image_data_url must be a base64 data URL")
    encoded = match.group("data").strip()
    padding = encoded.count("=")
    return math.floor(len(encoded) * 3 / 4) - padding
