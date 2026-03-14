from fastapi.responses import JSONResponse

from backend.database.connection import get_db_connection
from backend.repositories.chat_session_repository import get_session_by_id as get_session_by_id_record
from backend.schemas.estimate import (
    EstimateError,
    EstimateErrorField,
    EstimateRequest,
    EstimateResponse,
)
from backend.services.estimate import EstimateServiceError, estimate_meal
from backend.services.food_log_service import create_food_log_from_estimate


def create_estimate_response(
    request_model: EstimateRequest,
    user_id: int | None = None,
) -> tuple[int, EstimateResponse]:
    try:
        result = estimate_meal(request_model.query, request_model.profile_id, user_id)
        if user_id is not None:
            conn = get_db_connection()
            try:
                session_id = _resolve_food_log_session_id(
                    conn,
                    request_model.session_id,
                    user_id,
                )
                create_food_log_from_estimate(
                    user_id,
                    request_model.query,
                    result,
                    source_type="estimate_api",
                    session_id=session_id,
                    conn=conn,
                )
                conn.commit()
            except Exception:
                conn.rollback()
                raise
            finally:
                conn.close()
    except EstimateServiceError as exc:
        return exc.status_code, EstimateResponse(
            success=False,
            data=None,
            error=EstimateError(
                code=exc.code,
                message=exc.user_message,
                retryable=exc.retryable,
            ),
        )
    except Exception:
        return 500, EstimateResponse(
            success=False,
            data=None,
            error=EstimateError(
                code="INTERNAL_ERROR",
                message="浼扮畻鏈嶅姟鏆傛椂涓嶅彲鐢紝璇风◢鍚庨噸璇曘€?",
                retryable=True,
            ),
        )

    return 200, EstimateResponse(success=True, data=result, error=None)


def create_estimate_validation_error_response(errors: list[dict]) -> JSONResponse:
    fields = [
        EstimateErrorField(
            field=_format_field_name(error.get("loc", ())),
            message=_format_validation_message(error),
        )
        for error in errors
    ]
    payload = EstimateResponse(
        success=False,
        data=None,
        error=EstimateError(
            code="VALIDATION_ERROR",
            message="\u8bf7\u6c42\u53c2\u6570\u6821\u9a8c\u5931\u8d25\u3002",
            fields=fields,
            retryable=False,
        ),
    )
    return JSONResponse(status_code=422, content=payload.model_dump())


def _resolve_food_log_session_id(
    conn,
    session_id: int | None,
    user_id: int,
) -> int | None:
    if session_id is None:
        return None

    session = get_session_by_id_record(conn, session_id, user_id)
    if session is None:
        raise EstimateServiceError(
            code="SESSION_NOT_FOUND",
            status_code=404,
            message=f"Chat session {session_id} was not found for user {user_id}.",
            user_message="Chat session not found.",
            retryable=False,
        )
    return int(session["id"])


def _format_field_name(location: tuple[object, ...]) -> str:
    parts = [str(part) for part in location if part not in {"body"}]
    return ".".join(parts) or "body"


def _format_validation_message(error: dict) -> str:
    error_type = error.get("type")
    if error_type == "missing":
        return "\u7f3a\u5c11\u5fc5\u586b\u5b57\u6bb5"
    if error_type == "extra_forbidden":
        return "\u5305\u542b\u672a\u5b9a\u4e49\u5b57\u6bb5"
    if error_type == "string_type":
        return "\u5b57\u6bb5\u5fc5\u987b\u4e3a\u5b57\u7b26\u4e32"

    message = str(error.get("msg", "\u8f93\u5165\u4e0d\u5408\u6cd5"))
    prefix = "Value error, "
    if message.startswith(prefix):
        return message[len(prefix):]
    return message
