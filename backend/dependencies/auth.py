from fastapi import Depends, Header, HTTPException

from backend.schemas.user import UserOut
from backend.services.auth_security import TokenValidationError
from backend.services.auth_service import (
    InvalidCredentialsError,
    get_current_user as get_current_user_record,
)


def get_current_user(
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


def require_admin_user(
    user: UserOut = Depends(get_current_user),
) -> UserOut:
    if not user.is_admin:
        raise HTTPException(status_code=403, detail="Admin access required")
    return user
