from fastapi import APIRouter

from backend.schemas.estimate import EstimateRequest, EstimateResponse
from backend.services.estimate_service import create_estimate_response


router = APIRouter(prefix="/estimate", tags=["estimate"])


@router.post("", response_model=EstimateResponse)
def estimate(request_model: EstimateRequest) -> EstimateResponse:
    return create_estimate_response(request_model)
