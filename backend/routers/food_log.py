from fastapi import APIRouter, Depends

from backend.dependencies.auth import get_current_user
from backend.schemas.food_log import FoodLogEntryOut, parse_food_log_items
from backend.schemas.user import UserOut
from backend.services.food_log_service import list_food_logs_by_user


router = APIRouter(prefix="/food-log", tags=["food-log"])


@router.get("", response_model=list[FoodLogEntryOut])
def get_food_log_entries(
    current_user: UserOut = Depends(get_current_user),
) -> list[FoodLogEntryOut]:
    entries = list_food_logs_by_user(current_user.id)
    return [
        FoodLogEntryOut.model_validate(
            {
                "id": entry["id"],
                "source_type": entry["source_type"],
                "session_id": entry["session_id"],
                "source_message_id": entry["source_message_id"],
                "meal_description": entry["meal_description"],
                "logged_at": entry["logged_at"],
                "title": entry["result_title"],
                "confidence": entry["result_confidence"],
                "description": entry["result_description"],
                "items": parse_food_log_items(entry["ingredients_json"]),
                "total": entry["total_calories"],
                "suggestion": entry["assistant_suggestion"],
                "created_at": entry["created_at"],
                "updated_at": entry["updated_at"],
            }
        )
        for entry in entries
    ]
