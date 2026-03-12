from backend.schemas.estimate import EstimateError, EstimateRequest, EstimateResponse
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
