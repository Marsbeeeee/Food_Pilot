import sqlite3

from backend.schemas.auth import AuthResponse, LoginRequest, RegisterRequest
from backend.schemas.user import UserCreate, UserOut
from backend.services.auth_security import (
    TokenValidationError,
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)
from backend.services.user_service import (
    create_user,
    delete_user,
    get_user_auth_by_email,
    get_user_by_id,
)


class DuplicateEmailError(ValueError):
    pass


class InvalidCredentialsError(ValueError):
    pass


def register_user(request: RegisterRequest) -> AuthResponse:
    try:
        user = create_user(
            UserCreate(
                email=request.email,
                password_hash=hash_password(request.password),
                display_name=request.display_name,
            )
        )
    except sqlite3.IntegrityError as exc:
        raise DuplicateEmailError("email already exists") from exc

    return _build_auth_response(user)


def login_user(request: LoginRequest) -> AuthResponse:
    auth_row = get_user_auth_by_email(request.email)
    if auth_row is None:
        raise InvalidCredentialsError("invalid email or password")

    if not verify_password(request.password, auth_row["password_hash"]):
        raise InvalidCredentialsError("invalid email or password")

    user = get_user_by_id(auth_row["id"])
    if user is None:
        raise InvalidCredentialsError("invalid email or password")

    return _build_auth_response(user)


def get_current_user(token: str) -> UserOut:
    payload = decode_access_token(token)
    subject = payload.get("sub")
    if not isinstance(subject, str) or not subject.isdigit():
        raise TokenValidationError("invalid token subject")

    user = get_user_by_id(int(subject))
    if user is None:
        raise InvalidCredentialsError("user not found")
    return user


def delete_current_user(user_id: int) -> None:
    deleted = delete_user(user_id)
    if not deleted:
        raise InvalidCredentialsError("user not found")


def _build_auth_response(user: UserOut) -> AuthResponse:
    return AuthResponse(
        access_token=create_access_token(user.id),
        token_type="bearer",
        user=user,
    )
