from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.dependencies.auth import get_current_user
from backend.schemas.food_log import (
    FoodLogEntryOut,
    FoodLogFromEstimateRequest,
    FoodLogFromEstimateResponse,
    FoodLogListQuery,
    FoodLogPatchRequest,
    FoodLogSaveRequest,
    serialize_food_log_from_estimate_response,
    serialize_food_log_entry,
)
from backend.schemas.user import UserOut
from backend.services.food_log_service import (
    build_estimate_api_idempotency_key,
    create_food_log_from_estimate,
    delete_food_log,
    get_food_log_by_id,
    list_food_logs_by_user,
    restore_food_log,
    save_food_log,
    update_food_log_entry,
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
        query=filters.query,
        source_type=filters.source_type,
        has_image=filters.has_image,
        sort=filters.sort,
        limit=filters.limit,
    )
    return [serialize_food_log_entry(entry) for entry in entries]


@router.get("/{food_log_id}", response_model=FoodLogEntryOut, response_model_exclude_none=True)
def get_food_log_entry(
    food_log_id: int,
    current_user: UserOut = Depends(get_current_user),
) -> FoodLogEntryOut:
    entry = get_food_log_by_id(current_user.id, food_log_id)
    if entry is None:
        raise HTTPException(status_code=404, detail="Food log entry not found")
    return serialize_food_log_entry(entry)


@router.post("", response_model=FoodLogEntryOut, response_model_exclude_none=True)
def save_food_log_entry(
    request: FoodLogSaveRequest,
    current_user: UserOut = Depends(get_current_user),
) -> FoodLogEntryOut:
    try:
        entry = save_food_log(
            current_user.id,
            request.source_type,
            meal_description=request.meal_description,
            result_title=request.result_title,
            result_description=request.result_description,
            total_calories=request.total_calories,
            ingredients=[item.model_dump() for item in request.ingredients],
            food_log_id=request.food_log_id,
            session_id=request.session_id,
            source_message_id=request.source_message_id,
            result_confidence=request.result_confidence,
            assistant_suggestion=request.assistant_suggestion,
            meal_occurred_at=request.meal_occurred_at,
            status=request.status or "active",
            idempotency_key=request.idempotency_key,
            is_manual=request.is_manual,
            image=request.image,
            image_source=request.image_source,
            image_license=request.image_license,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return serialize_food_log_entry(entry)


@router.patch("/{food_log_id}", response_model=FoodLogEntryOut, response_model_exclude_none=True)
def patch_food_log_entry(
    food_log_id: int,
    request: FoodLogPatchRequest,
    current_user: UserOut = Depends(get_current_user),
) -> FoodLogEntryOut:
    try:
        entry = update_food_log_entry(
            current_user.id,
            food_log_id,
            meal_description=request.meal_description,
            result_title=request.result_title,
            result_confidence=request.result_confidence,
            result_description=request.result_description,
            total_calories=request.total_calories,
            ingredients=(
                [item.model_dump() for item in request.ingredients]
                if request.ingredients is not None
                else None
            ),
            assistant_suggestion=request.assistant_suggestion,
            meal_occurred_at=request.meal_occurred_at,
            image=request.image,
            image_source=request.image_source,
            image_license=request.image_license,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return serialize_food_log_entry(entry)


@router.post(
    "/from-estimate",
    response_model=FoodLogFromEstimateResponse,
    response_model_exclude_none=True,
)
def save_food_log_from_estimate_entry(
    request: FoodLogFromEstimateRequest,
    current_user: UserOut = Depends(get_current_user),
) -> FoodLogFromEstimateResponse:
    try:
        entry = create_food_log_from_estimate(
            current_user.id,
            request.meal_description,
            request.estimate,
            source_type="estimate_api",
            meal_occurred_at=request.meal_occurred_at,
            idempotency_key=build_estimate_api_idempotency_key(request.client_request_id),
            image=request.image,
            image_source=request.image_source,
            image_license=request.image_license,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    return serialize_food_log_from_estimate_response(
        entry,
        client_request_id=request.client_request_id,
    )


@router.post(
    "/{food_log_id}/restore",
    response_model=FoodLogEntryOut,
    response_model_exclude_none=True,
)
def restore_saved_food_log_entry(
    food_log_id: int,
    current_user: UserOut = Depends(get_current_user),
) -> FoodLogEntryOut:
    try:
        entry = restore_food_log(current_user.id, food_log_id)
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
