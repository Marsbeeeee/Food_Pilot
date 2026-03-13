import sqlite3

from fastapi import APIRouter, Depends, HTTPException

from backend.dependencies.auth import get_current_user
from backend.schemas.profile import ProfileIn, ProfileOut
from backend.schemas.user import UserOut
from backend.services.profile_service import (
    create_profile as create_profile_record,
    get_profile as get_profile_record,
    get_profile_by_user_id as get_profile_by_user_id_record,
    update_profile as update_profile_record,
)

router = APIRouter(prefix="/profile", tags=["profile"])


@router.post("", response_model=ProfileOut, status_code=201)
def create_profile(
    profile: ProfileIn,
    current_user: UserOut = Depends(get_current_user),
):
    try:
        return create_profile_record(current_user.id, profile)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=409, detail="Profile already exists") from exc


@router.get("/me", response_model=ProfileOut)
def get_my_profile(current_user: UserOut = Depends(get_current_user)):
    profile = get_profile_by_user_id_record(current_user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.get("/{profile_id}", response_model=ProfileOut)
def get_profile(
    profile_id: int,
    current_user: UserOut = Depends(get_current_user),
):
    profile = get_profile_record(profile_id, current_user.id)
    if profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return profile


@router.put("/{profile_id}", response_model=ProfileOut)
def update_profile(
    profile_id: int,
    profile: ProfileIn,
    current_user: UserOut = Depends(get_current_user),
):
    updated_profile = update_profile_record(profile_id, current_user.id, profile)
    if updated_profile is None:
        raise HTTPException(status_code=404, detail="Profile not found")
    return updated_profile
