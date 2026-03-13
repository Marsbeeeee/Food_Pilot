import unittest
from unittest.mock import patch

from fastapi import HTTPException

from backend.routers.chat import (
    create_chat_message,
    create_chat_session,
    delete_chat_session,
    get_chat_session,
    list_chat_sessions,
    rename_chat_session,
    send_chat_message,
)
from backend.schemas.chat import ChatSendMessageRequest, RenameSessionRequest
from backend.schemas.user import UserOut


class ChatRouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.user = UserOut.model_validate(
            {
                "id": 1,
                "email": "alice@example.com",
                "display_name": "Alice",
                "created_at": "2026-03-13 18:00:00",
                "updated_at": "2026-03-13 18:00:00",
            }
        )

    def test_create_chat_session_returns_created_session(self) -> None:
        with patch(
            "backend.routers.chat.create_empty_session",
            return_value=build_session_summary(),
        ):
            response = create_chat_session(self.user)

        self.assertEqual(response.id, 1)
        self.assertEqual(response.title, "New chat")

    def test_get_chat_session_maps_missing_session_to_404(self) -> None:
        with patch("backend.routers.chat.get_session_detail", return_value=None):
            with self.assertRaises(HTTPException) as exc:
                get_chat_session(99, self.user)

        self.assertEqual(exc.exception.status_code, 404)

    def test_rename_chat_session_maps_missing_session_to_404(self) -> None:
        request = RenameSessionRequest.model_validate({"title": "Renamed"})

        with patch("backend.routers.chat.rename_session", return_value=None):
            with self.assertRaises(HTTPException) as exc:
                rename_chat_session(99, request, self.user)

        self.assertEqual(exc.exception.status_code, 404)

    def test_delete_chat_session_maps_missing_session_to_404(self) -> None:
        with patch("backend.routers.chat.delete_session", return_value=False):
            with self.assertRaises(HTTPException) as exc:
                delete_chat_session(99, self.user)

        self.assertEqual(exc.exception.status_code, 404)

    def test_list_chat_sessions_returns_serialized_summaries(self) -> None:
        with patch(
            "backend.routers.chat.list_user_sessions",
            return_value=[build_session_summary(), build_session_summary(session_id=2, title="Lunch")],
        ):
            response = list_chat_sessions(self.user)

        self.assertEqual(len(response), 2)
        self.assertEqual(response[1].title, "Lunch")

    def test_send_chat_message_returns_exchange_response(self) -> None:
        request = ChatSendMessageRequest.model_validate({"content": "chicken salad"})

        with patch(
            "backend.routers.chat.send_message_in_session",
            return_value=build_exchange(),
        ):
            response = send_chat_message(1, request, self.user)

        self.assertEqual(response.session.id, 1)
        self.assertEqual(response.user_message.role, "user")
        self.assertEqual(response.assistant_message.message_type, "estimate_result")

    def test_create_chat_message_creates_session_and_returns_exchange_response(self) -> None:
        request = ChatSendMessageRequest.model_validate({"content": "oatmeal"})

        with patch(
            "backend.routers.chat.create_session_and_reply",
            return_value=build_exchange(user_message=build_user_message(content="oatmeal")),
        ):
            response = create_chat_message(request, self.user)

        self.assertEqual(response.session.id, 1)
        self.assertEqual(response.user_message.content, "oatmeal")

    def test_send_chat_message_maps_missing_session_to_404(self) -> None:
        request = ChatSendMessageRequest.model_validate({"content": "chicken salad"})

        with patch("backend.routers.chat.send_message_in_session", return_value=None):
            with self.assertRaises(HTTPException) as exc:
                send_chat_message(99, request, self.user)

        self.assertEqual(exc.exception.status_code, 404)


def build_session_summary(
    *,
    session_id: int = 1,
    title: str = "New chat",
) -> dict:
    return {
        "id": session_id,
        "title": title,
        "created_at": "2026-03-13 18:00:00",
        "updated_at": "2026-03-13 18:00:00",
        "last_message_at": "2026-03-13 18:00:00",
    }


def build_user_message(*, content: str = "chicken salad") -> dict:
    return {
        "id": 10,
        "session_id": 1,
        "role": "user",
        "message_type": "text",
        "content": content,
        "result_title": None,
        "result_confidence": None,
        "result_description": None,
        "result_items_json": None,
        "result_total": None,
        "created_at": "2026-03-13 18:01:00",
    }


def build_assistant_result_message() -> dict:
    return {
        "id": 11,
        "session_id": 1,
        "role": "assistant",
        "message_type": "estimate_result",
        "content": "A lighter dressing would reduce calories.",
        "result_title": "Chicken salad",
        "result_confidence": "high",
        "result_description": "Protein-forward salad with avocado.",
        "result_items_json": '[{"name":"Chicken","portion":"150g","energy":"240 kcal"}]',
        "result_total": "240 kcal",
        "created_at": "2026-03-13 18:01:05",
    }


def build_session_detail(*, messages: list[dict] | None = None) -> dict:
    detail = build_session_summary()
    detail["messages"] = messages or [build_user_message(), build_assistant_result_message()]
    return detail


def build_exchange(
    *,
    session: dict | None = None,
    user_message: dict | None = None,
    assistant_message: dict | None = None,
) -> dict:
    return {
        "session": session or build_session_detail(),
        "user_message": user_message or build_user_message(),
        "assistant_message": assistant_message or build_assistant_result_message(),
    }


if __name__ == "__main__":
    unittest.main()
