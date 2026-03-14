from typing import Annotated

from fastapi import APIRouter, Depends

from backend.dependencies.auth import get_current_user
from backend.schemas.food_log import (
    FoodLogEntryOut,
    FoodLogListQuery,
    serialize_food_log_entry,
)
from backend.schemas.user import UserOut
from backend.services.food_log_service import list_food_logs_by_user


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
