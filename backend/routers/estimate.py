from fastapi import APIRouter, Body, status
from fastapi.responses import JSONResponse
from pydantic import ValidationError

from backend.schemas.estimate import (
    EstimateError,
    EstimateErrorField,
    EstimateRequest,
    EstimateResponse,
)
from backend.services.estimate_service import EstimateServiceError, estimate_meal


router = APIRouter(prefix="/estimate", tags=["estimate"])


@router.post("", response_model=EstimateResponse)
def estimate(payload: object = Body(default=None)):
    try:
        request_model = EstimateRequest.model_validate(payload)
    except ValidationError as exc:
        fields = [
            EstimateErrorField(
                field=_format_field_name(error.get("loc", ())),
                message=_format_validation_message(error),
            )
            for error in exc.errors()
        ]
        return _error_response(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            fields=fields,
            retryable=False,
        )

    try:
        result = estimate_meal(request_model.query)
    except EstimateServiceError as exc:
        return _error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            retryable=exc.retryable,
        )
    except Exception:
        return _error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            code="INTERNAL_ERROR",
            message="The estimate service is temporarily unavailable. Please try again later.",
            retryable=True,
        )

    return EstimateResponse(success=True, data=result, error=None)


def _error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    retryable: bool,
    fields: list[EstimateErrorField] | None = None,
) -> JSONResponse:
    payload = EstimateResponse(
        success=False,
        data=None,
        error=EstimateError(
            code=code,
            message=message,
            fields=fields,
            retryable=retryable,
        ),
    )
    return JSONResponse(status_code=status_code, content=payload.model_dump())


def _format_field_name(location: tuple[object, ...]) -> str:
    parts = [str(part) for part in location if part not in {"body"}]
    return ".".join(parts) or "body"


def _format_validation_message(error: dict) -> str:
    error_type = error.get("type")
    if error_type == "missing":
        return "Missing required field"
    if error_type == "extra_forbidden":
        return "Unexpected field"
    if error_type == "string_type":
        return "Field must be a string"

    message = str(error.get("msg", "Invalid input"))
    prefix = "Value error, "
    if message.startswith(prefix):
        return message[len(prefix):]
    return message
