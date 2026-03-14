from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.dependencies.auth import get_current_user
from backend.schemas.food_log import (
    FoodLogEntryOut,
    FoodLogListQuery,
    FoodLogSaveRequest,
    serialize_food_log_entry,
)
from backend.schemas.user import UserOut
from backend.services.food_log_service import (
    delete_food_log,
    list_food_logs_by_user,
    save_food_log,
)


router = APIRouter(prefix="/food-logs", tags=["food-logs"])


@router.get("", response_model=list[FoodLogEntryOut], response_model_exclude_none=True)
def list_food_log_entries(
    filters: Annotated[FoodLogListQuery, Depends()],
    current_user: UserOut = Depends(get_current_user),
) -> list[FoodLogEntryOut]:
    entries = list_food_logs_by_user(
        current_user.id,
        session_id=filters.session_id,
        date_from=filters.date_from,
        date_to=filters.date_to,
        meal=filters.meal,
        limit=filters.limit,
    )
    return [serialize_food_log_entry(entry) for entry in entries]


@router.post("", response_model=FoodLogEntryOut, response_model_exclude_none=True)
def save_food_log_entry(
    request: FoodLogSaveRequest,
    current_user: UserOut = Depends(get_current_user),
) -> FoodLogEntryOut:
    # Food Log exposes save-only writes. Updating a saved item must happen by
    # saving a fresh analysis, which then overwrites the matching favorite.
    try:
        entry = save_food_log(
            current_user.id,
            request.source_type,
            meal_description=request.meal_description,
            result_title=request.result_title,
            result_description=request.result_description,
            total_calories=request.total_calories,
            ingredients=[item.model_dump() for item in request.ingredients],
            session_id=request.session_id,
            source_message_id=request.source_message_id,
            result_confidence=request.result_confidence,
            assistant_suggestion=request.assistant_suggestion,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return serialize_food_log_entry(entry)


@router.delete("/{food_log_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_saved_food_log_entry(
    food_log_id: int,
    current_user: UserOut = Depends(get_current_user),
):
    deleted = delete_food_log(current_user.id, food_log_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Food log entry not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
