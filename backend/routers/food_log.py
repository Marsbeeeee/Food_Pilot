from fastapi import APIRouter, Depends

from backend.dependencies.auth import get_current_user
from backend.schemas.food_log import FoodLogEntryOut, parse_food_log_items
from backend.schemas.user import UserOut
from backend.services.food_log_service import list_food_log_entries


router = APIRouter(prefix="/food-log", tags=["food-log"])


@router.get("", response_model=list[FoodLogEntryOut])
def get_food_log_entries(
    current_user: UserOut = Depends(get_current_user),
) -> list[FoodLogEntryOut]:
    entries = list_food_log_entries(current_user.id)
    return [
        FoodLogEntryOut.model_validate(
            {
                "id": entry["id"],
                "source_type": entry["source_type"],
                "session_id": entry["session_id"],
                "message_id": entry["message_id"],
                "title": entry["title"],
                "confidence": entry["confidence"],
                "description": entry["description"],
                "items": parse_food_log_items(entry["items_json"]),
                "total": entry["total"],
                "suggestion": entry["suggestion"],
                "created_at": entry["created_at"],
            }
        )
        for entry in entries
    ]
