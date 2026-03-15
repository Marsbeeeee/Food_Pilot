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
    create_empty_session,
    create_session_and_reply,
    delete_session,
    get_session_detail,
    list_user_sessions,
    rename_session,
    send_message_in_session,
)


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
    exchange = send_message_in_session(
        current_user.id,
        session_id,
        request.content,
        profile_id=request.profile_id,
    )
    if exchange is None:
        raise HTTPException(status_code=404, detail="Chat session not found")

    return ChatMessageExchangeResponse(
        session=_serialize_session_summary(exchange["session"]),
        user_message=_serialize_message(exchange["user_message"]),
        assistant_message=_serialize_message(exchange["assistant_message"]),
    )


@router.post("/messages", response_model=ChatMessageExchangeResponse, status_code=status.HTTP_201_CREATED)
def create_chat_message(
    request: ChatSendMessageRequest,
    current_user: UserOut = Depends(get_current_user),
):
    exchange = create_session_and_reply(
        current_user.id,
        request.content,
        profile_id=request.profile_id,
    )

    return ChatMessageExchangeResponse(
        session=_serialize_session_summary(exchange["session"]),
        user_message=_serialize_message(exchange["user_message"]),
        assistant_message=_serialize_message(exchange["assistant_message"]),
    )


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
            "message_type": _serialize_message_type(message["message_type"]),
            "content": message["content"],
            "payload": _parse_payload_json(message.get("payload_json")),
            "result_title": message["result_title"],
            "result_confidence": message["result_confidence"],
            "result_description": message["result_description"],
            "result_items": parse_result_items(message["result_items_json"]),
            "result_total": message["result_total"],
            "created_at": message["created_at"],
        }
    )


def _serialize_message_type(message_type: object) -> str:
    if message_type == "estimate_result":
        return "meal_estimate"
    if message_type == "text":
        return "text"
    if isinstance(message_type, str):
        return message_type
    raise ValueError("message_type must be a string")


def _parse_payload_json(value: object) -> dict[str, object] | None:
    if not isinstance(value, str) or not value.strip():
        return None

    try:
        payload = json.loads(value)
    except json.JSONDecodeError:
        return None

    if not isinstance(payload, dict):
        return None

    return payload
