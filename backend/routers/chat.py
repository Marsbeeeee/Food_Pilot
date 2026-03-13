import json

from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.dependencies.auth import get_current_user
from backend.schemas.chat import (
    ChatMessageExchangeResponse,
    ChatMessageOut,
    ChatSendMessageRequest,
    ChatSessionDetail,
    ChatSessionSummary,
    RenameSessionRequest,
    parse_result_items,
)
from backend.schemas.user import UserOut
from backend.services.chat_service import (
    append_assistant_message,
    append_user_message,
    create_empty_session,
    create_session_with_first_user_message,
    delete_session,
    get_session_detail,
    list_user_sessions,
    rename_session,
)
from backend.services.estimate import estimate_meal


router = APIRouter(prefix="/chat", tags=["chat"])


@router.post("/sessions", response_model=ChatSessionSummary, status_code=status.HTTP_201_CREATED)
def create_chat_session(current_user: UserOut = Depends(get_current_user)):
    session = create_empty_session(current_user.id)
    return _serialize_session_summary(session)


@router.get("/sessions", response_model=list[ChatSessionSummary])
def list_chat_sessions(current_user: UserOut = Depends(get_current_user)):
    sessions = list_user_sessions(current_user.id)
    return [_serialize_session_summary(session) for session in sessions]


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
def get_chat_session(
    session_id: int,
    current_user: UserOut = Depends(get_current_user),
):
    session = get_session_detail(current_user.id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return _serialize_session_detail(session)


@router.patch("/sessions/{session_id}", response_model=ChatSessionSummary)
def rename_chat_session(
    session_id: int,
    request: RenameSessionRequest,
    current_user: UserOut = Depends(get_current_user),
):
    session = rename_session(current_user.id, session_id, request.title)
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return _serialize_session_summary(session)


@router.delete("/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_chat_session(
    session_id: int,
    current_user: UserOut = Depends(get_current_user),
):
    deleted = delete_session(current_user.id, session_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.post("/sessions/{session_id}/messages", response_model=ChatMessageExchangeResponse)
def send_chat_message(
    session_id: int,
    request: ChatSendMessageRequest,
    current_user: UserOut = Depends(get_current_user),
):
    user_message = append_user_message(
        current_user.id,
        session_id,
        request.content,
    )
    if user_message is None:
        raise HTTPException(status_code=404, detail="Chat session not found")

    assistant_message = _generate_and_store_assistant_reply(
        current_user.id,
        session_id,
        request.content,
        request.profile_id,
    )
    session = _require_session_summary(current_user.id, session_id)

    return ChatMessageExchangeResponse(
        session=_serialize_session_summary(session),
        user_message=_serialize_message(user_message),
        assistant_message=_serialize_message(assistant_message),
    )


@router.post("/messages", response_model=ChatMessageExchangeResponse, status_code=status.HTTP_201_CREATED)
def create_chat_message(
    request: ChatSendMessageRequest,
    current_user: UserOut = Depends(get_current_user),
):
    session_detail = create_session_with_first_user_message(current_user.id, request.content)
    session_id = int(session_detail["id"])
    user_message = session_detail["messages"][0]

    assistant_message = _generate_and_store_assistant_reply(
        current_user.id,
        session_id,
        request.content,
        request.profile_id,
    )
    session = _require_session_summary(current_user.id, session_id)

    return ChatMessageExchangeResponse(
        session=_serialize_session_summary(session),
        user_message=_serialize_message(user_message),
        assistant_message=_serialize_message(assistant_message),
    )


def _generate_and_store_assistant_reply(
    user_id: int,
    session_id: int,
    content: str,
    profile_id: int | None,
) -> dict[str, object]:
    try:
        estimate = estimate_meal(content, profile_id, user_id)
        assistant_message = append_assistant_message(
            user_id,
            session_id,
            message_type="estimate_result",
            content=estimate.suggestion,
            result_title=estimate.title,
            result_confidence=estimate.confidence,
            result_description=estimate.description,
            result_items_json=json.dumps(
                [item.model_dump() for item in estimate.items],
                ensure_ascii=False,
            ),
            result_total=estimate.total_calories,
        )
        if assistant_message is None:
            raise HTTPException(status_code=404, detail="Chat session not found")
        return assistant_message
    except Exception as exc:
        fallback_message = _build_fallback_message(exc)
        assistant_message = append_assistant_message(
            user_id,
            session_id,
            content=fallback_message,
        )
        if assistant_message is None:
            raise HTTPException(status_code=404, detail="Chat session not found") from exc
        return assistant_message


def _build_fallback_message(error: Exception) -> str:
    user_message = getattr(error, "user_message", None)
    if isinstance(user_message, str) and user_message.strip():
        return user_message
    return "Unable to process this meal description right now. Please try again."


def _require_session_summary(user_id: int, session_id: int) -> dict[str, object]:
    session = get_session_detail(user_id, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Chat session not found")
    return session


def _serialize_session_summary(session: dict[str, object]) -> ChatSessionSummary:
    return ChatSessionSummary.model_validate(
        {
            "id": session["id"],
            "title": session["title"],
            "created_at": session["created_at"],
            "updated_at": session["updated_at"],
            "last_message_at": session["last_message_at"],
        }
    )


def _serialize_session_detail(session: dict[str, object]) -> ChatSessionDetail:
    return ChatSessionDetail.model_validate(
        {
            "id": session["id"],
            "title": session["title"],
            "created_at": session["created_at"],
            "updated_at": session["updated_at"],
            "last_message_at": session["last_message_at"],
            "messages": [_serialize_message(message) for message in session["messages"]],
        }
    )


def _serialize_message(message: dict[str, object]) -> ChatMessageOut:
    return ChatMessageOut.model_validate(
        {
            "id": message["id"],
            "session_id": message["session_id"],
            "role": message["role"],
            "message_type": message["message_type"],
            "content": message["content"],
            "result_title": message["result_title"],
            "result_confidence": message["result_confidence"],
            "result_description": message["result_description"],
            "result_items": parse_result_items(message["result_items_json"]),
            "result_total": message["result_total"],
            "created_at": message["created_at"],
        }
    )
