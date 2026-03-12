from fastapi import APIRouter, Response

from backend.schemas.estimate import EstimateRequest, EstimateResponse
from backend.services.estimate_service import create_estimate_response


router = APIRouter(prefix="/estimate", tags=["estimate"])


@router.post("", response_model=EstimateResponse)
def estimate(
    request_model: EstimateRequest,
    response: Response,
) -> EstimateResponse:
    status_code, payload = create_estimate_response(request_model)
    response.status_code = status_code
    return payload
