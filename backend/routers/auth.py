from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.dependencies.auth import get_current_user
from backend.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from backend.schemas.user import UserOut
from backend.services.auth_service import (
    DuplicateEmailError,
    InvalidCredentialsError,
    delete_current_user,
    login_user,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=AuthResponse, status_code=201)
def register(request: RegisterRequest):
    try:
        return register_user(request)
    except DuplicateEmailError as exc:
        raise HTTPException(status_code=409, detail="Email already exists") from exc


@router.post("/login", response_model=AuthResponse)
def login(request: LoginRequest):
    try:
        return login_user(request)
    except InvalidCredentialsError as exc:
        raise HTTPException(status_code=401, detail="Invalid email or password") from exc


@router.get("/me", response_model=UserOut)
def get_me(user: UserOut = Depends(get_current_user)):
    return user


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
def delete_me(user: UserOut = Depends(get_current_user)):
    delete_current_user(user.id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
