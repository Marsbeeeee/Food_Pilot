from fastapi import APIRouter, Depends, Header, HTTPException

from backend.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from backend.schemas.user import UserOut
from backend.services.auth_security import TokenValidationError
from backend.services.auth_service import (
    DuplicateEmailError,
    InvalidCredentialsError,
    get_current_user as get_current_user_record,
    login_user,
    register_user,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def _get_current_user_from_header(
    authorization: str | None = Header(default=None),
) -> UserOut:
    if authorization is None:
        raise HTTPException(status_code=401, detail="Authorization header is required")

    scheme, _, token = authorization.partition(" ")
    if scheme.lower() != "bearer" or not token:
        raise HTTPException(status_code=401, detail="Invalid authorization header")

    try:
        return get_current_user_record(token)
    except (InvalidCredentialsError, TokenValidationError) as exc:
        raise HTTPException(status_code=401, detail="Invalid or expired token") from exc


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
def get_me(user: UserOut = Depends(_get_current_user_from_header)):
    return user
