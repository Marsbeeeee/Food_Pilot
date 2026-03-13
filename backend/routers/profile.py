from fastapi import APIRouter, HTTPException
from backend.schemas.profile import ProfileIn, ProfileOut
from backend.services.profile_service import (
    create_profile as create_profile_record,
    get_profile as get_profile_record,
    update_profile as update_profile_record,
)

router = APIRouter(prefix = "/profile", tags = ["profile"])

@router.post("", response_model = ProfileOut)
def create_profile(profile: ProfileIn):
    return create_profile_record(profile)


@router.get("/{profile_id}", response_model = ProfileOut)
def get_profile(profile_id: int):
    profile = get_profile_record(profile_id)
    if profile is None:
        raise HTTPException(status_code = 404, detail = "Profile not found")
    return profile


@router.put("/{profile_id}", response_model = ProfileOut)
def update_profile(profile_id: int, profile: ProfileIn):
    updated_profile = update_profile_record(profile_id, profile)
    if updated_profile is None:
        raise HTTPException(status_code = 404, detail = "Profile not found")
    return updated_profile

@router.post("/echo")
def echo_profile(profile: ProfileIn):
    return profile
