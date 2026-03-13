from fastapi import APIRouter, Depends, Response

from backend.dependencies.auth import get_current_user
from backend.schemas.estimate import EstimateRequest, EstimateResponse
from backend.schemas.user import UserOut
from backend.services.estimate_service import create_estimate_response


router = APIRouter(prefix="/estimate", tags=["estimate"])


@router.post("", response_model=EstimateResponse)
def estimate(
    request_model: EstimateRequest,
    response: Response,
    current_user: UserOut = Depends(get_current_user),
) -> EstimateResponse:
    status_code, payload = create_estimate_response(request_model, current_user.id)
    response.status_code = status_code
    return payload
