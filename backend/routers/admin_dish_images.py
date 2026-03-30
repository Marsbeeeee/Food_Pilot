from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies.auth import require_admin_user
from backend.schemas.admin_dish_image import (
    AdminDishImageActionRequest,
    AdminDishImageDetailOut,
    AdminDishImageGenerationJobListQuery,
    AdminDishImageGenerationJobOut,
    AdminDishImageListItemOut,
    AdminDishImageListQuery,
)
from backend.schemas.user import UserOut
from backend.services.admin_dish_image_service import (
    approve_admin_dish_image_candidate,
    get_admin_dish_image_candidate,
    list_admin_dish_image_candidates,
    list_admin_active_generation_jobs,
    regenerate_admin_dish_image_candidate,
    reject_and_regenerate_admin_dish_image_candidate,
    reject_admin_dish_image_candidate,
)


router = APIRouter(prefix="/admin/dish-images", tags=["admin-dish-images"])


@router.get("", response_model=list[AdminDishImageListItemOut], response_model_exclude_none=True)
def list_dish_image_review_candidates(
    filters: Annotated[AdminDishImageListQuery, Depends()],
    _: UserOut = Depends(require_admin_user),
) -> list[AdminDishImageListItemOut]:
    try:
        items = list_admin_dish_image_candidates(
            status=filters.status,
            query=filters.query,
            created_from=filters.created_from,
            created_to=filters.created_to,
            limit=filters.limit,
        )
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [AdminDishImageListItemOut.model_validate(item) for item in items]


@router.get(
    "/generation-jobs",
    response_model=list[AdminDishImageGenerationJobOut],
    response_model_exclude_none=True,
)
def list_dish_image_generation_jobs(
    filters: Annotated[AdminDishImageGenerationJobListQuery, Depends()],
    _: UserOut = Depends(require_admin_user),
) -> list[AdminDishImageGenerationJobOut]:
    try:
        items = list_admin_active_generation_jobs(limit=filters.limit)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return [AdminDishImageGenerationJobOut.model_validate(item) for item in items]


@router.get("/{dish_image_id}", response_model=AdminDishImageDetailOut, response_model_exclude_none=True)
def get_dish_image_review_candidate(
    dish_image_id: int,
    _: UserOut = Depends(require_admin_user),
) -> AdminDishImageDetailOut:
    item = get_admin_dish_image_candidate(dish_image_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Dish image candidate not found")
    return AdminDishImageDetailOut.model_validate(item)


@router.post("/{dish_image_id}/approve", response_model=AdminDishImageDetailOut, response_model_exclude_none=True)
def approve_dish_image_review_candidate(
    dish_image_id: int,
    request: AdminDishImageActionRequest,
    admin_user: UserOut = Depends(require_admin_user),
) -> AdminDishImageDetailOut:
    try:
        item = approve_admin_dish_image_candidate(
            admin_user_id=admin_user.id,
            dish_image_id=dish_image_id,
            note=request.note,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AdminDishImageDetailOut.model_validate(item)


@router.post("/{dish_image_id}/reject", response_model=AdminDishImageDetailOut, response_model_exclude_none=True)
def reject_dish_image_review_candidate(
    dish_image_id: int,
    request: AdminDishImageActionRequest,
    admin_user: UserOut = Depends(require_admin_user),
) -> AdminDishImageDetailOut:
    try:
        item = reject_admin_dish_image_candidate(
            admin_user_id=admin_user.id,
            dish_image_id=dish_image_id,
            note=request.note,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AdminDishImageDetailOut.model_validate(item)


@router.post("/{dish_image_id}/regenerate", response_model=AdminDishImageDetailOut, response_model_exclude_none=True)
def regenerate_dish_image_review_candidate(
    dish_image_id: int,
    request: AdminDishImageActionRequest,
    admin_user: UserOut = Depends(require_admin_user),
) -> AdminDishImageDetailOut:
    try:
        item = regenerate_admin_dish_image_candidate(
            admin_user_id=admin_user.id,
            dish_image_id=dish_image_id,
            note=request.note,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AdminDishImageDetailOut.model_validate(item)


@router.post(
    "/{dish_image_id}/reject-and-regenerate",
    response_model=AdminDishImageDetailOut,
    response_model_exclude_none=True,
)
def reject_and_regenerate_dish_image_review_candidate(
    dish_image_id: int,
    request: AdminDishImageActionRequest,
    admin_user: UserOut = Depends(require_admin_user),
) -> AdminDishImageDetailOut:
    try:
        item = reject_and_regenerate_admin_dish_image_candidate(
            admin_user_id=admin_user.id,
            dish_image_id=dish_image_id,
            note=request.note,
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return AdminDishImageDetailOut.model_validate(item)
