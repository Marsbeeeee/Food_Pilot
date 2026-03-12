from fastapi.responses import JSONResponse

from backend.schemas.estimate import (
    EstimateError,
    EstimateErrorField,
    EstimateRequest,
    EstimateResponse,
)
from backend.services.estimate import EstimateServiceError, estimate_meal


def create_estimate_response(request_model: EstimateRequest) -> EstimateResponse:
    try:
        result = estimate_meal(request_model.query)
    except EstimateServiceError as exc:
        return EstimateResponse(
            success=False,
            data=None,
            error=EstimateError(
                code=exc.code,
                message=exc.message,
                retryable=exc.retryable,
            ),
        )
    except Exception:
        return EstimateResponse(
            success=False,
            data=None,
            error=EstimateError(
                code="INTERNAL_ERROR",
                message="The estimate service is temporarily unavailable. Please try again later.",
                retryable=True,
            ),
        )

    return EstimateResponse(success=True, data=result, error=None)


def create_estimate_validation_error_response(errors: list[dict]) -> JSONResponse:
    fields = [
        EstimateErrorField(
            field=_format_field_name(error.get("loc", ())),
            message=_format_validation_message(error),
        )
        for error in errors
    ]
    payload = EstimateResponse(
        success=False,
        data=None,
        error=EstimateError(
            code="VALIDATION_ERROR",
            message="Request validation failed.",
            fields=fields,
            retryable=False,
        ),
    )
    return JSONResponse(status_code=422, content=payload.model_dump())


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
