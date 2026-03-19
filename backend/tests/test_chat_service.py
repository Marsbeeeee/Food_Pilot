import os
import sqlite3
import unittest
from unittest.mock import patch
import json

from backend.database.connection import get_db_connection
from backend.database.init_db import init_db
from backend.schemas.recommendation import GuidanceReply
from backend.services.food_log_service import save_food_log
from backend.services.chat_service import (
    CLARIFICATION_MESSAGE,
    DEFAULT_SESSION_TITLE,
    DEFAULT_ASSISTANT_ERROR_MESSAGE,
    DEFAULT_RECOMMENDATION_ERROR_MESSAGE,
    append_assistant_message,
    append_user_message,
    create_empty_session,
    create_session_and_reply,
    create_session_with_first_user_message,
    delete_session,
    get_session_detail,
    list_user_sessions,
    rename_session,
    resolve_message_type,
    send_message_in_session,
)


class ChatServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = os.path.join(
            os.getcwd(),
            "backend",
            "database",
            "test_chat_service.db",
        )
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db_patch = patch("backend.database.connection.db_path", self.db_path)
        self.db_patch.start()
        init_db()

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO users (email, password_hash, display_name)
                VALUES (?, ?, ?)
                """,
                ("owner@example.com", "hashed-password", "Owner"),
            )
            self.user_id = cursor.lastrowid

            cursor.execute(
                """
                INSERT INTO users (email, password_hash, display_name)
                VALUES (?, ?, ?)
                """,
                ("other@example.com", "hashed-password", "Other"),
            )
            self.other_user_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()

    def tearDown(self) -> None:
        self.db_patch.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_create_empty_session_uses_default_title(self) -> None:
        created = create_empty_session(self.user_id)

        self.assertEqual(created["title"], DEFAULT_SESSION_TITLE)

    def test_create_session_with_first_user_message_sets_title_and_detail(self) -> None:
        detail = create_session_with_first_user_message(
            self.user_id,
            "  chicken salad with avocado and egg  ",
        )

        self.assertEqual(detail["title"], "chicken salad with avocado and egg")
        self.assertEqual(len(detail["messages"]), 1)
        self.assertEqual(detail["messages"][0]["role"], "user")

    def test_append_user_message_renames_empty_session_using_first_message_only(self) -> None:
        session = create_empty_session(self.user_id)

        first_message = append_user_message(
            self.user_id,
            int(session["id"]),
            "first meal note",
        )
        second_message = append_user_message(
            self.user_id,
            int(session["id"]),
            "second meal note",
        )
        detail = get_session_detail(self.user_id, int(session["id"]))

        self.assertIsNotNone(first_message)
        self.assertIsNotNone(second_message)
        self.assertEqual(detail["title"], "first meal note")
        self.assertEqual(len(detail["messages"]), 2)

    def test_append_assistant_message_supports_text_and_result_message(self) -> None:
        detail = create_session_with_first_user_message(self.user_id, "oatmeal")
        session_id = int(detail["id"])

        text_message = append_assistant_message(
            self.user_id,
            session_id,
            content="Estimated around 320 kcal.",
        )
        result_message = append_assistant_message(
            self.user_id,
            session_id,
            message_type="estimate_result",
            content="A smaller portion would reduce calories.",
            result_title="Oatmeal bowl",
            result_confidence="high",
            result_description="Balanced breakfast with fruit.",
            result_items_json='[{"name":"Oats","portion":"60g","energy":"230 kcal"}]',
            result_total="320 kcal",
        )
        refreshed = get_session_detail(self.user_id, session_id)

        self.assertEqual(text_message["message_type"], "text")
        self.assertEqual(result_message["message_type"], "estimate_result")
        self.assertEqual(len(refreshed["messages"]), 3)
        self.assertEqual(refreshed["messages"][-1]["result_total"], "320 kcal")

    def test_resolve_message_type_routes_typical_recommendation_requests(self) -> None:
        resolved = resolve_message_type(
            "帮我推荐一个更轻一点的晚餐",
            profile_id=12,
            user_id=self.user_id,
        )

        self.assertEqual(resolved, "meal_recommendation")

    def test_resolve_message_type_routes_comparison_request_to_recommendation(self) -> None:
        resolved = resolve_message_type(
            "汉堡和鸡肉沙拉哪个更适合我今天晚饭？",
            profile_id=12,
            user_id=self.user_id,
        )

        self.assertEqual(resolved, "meal_recommendation")

    def test_resolve_message_type_routes_swap_and_worth_choice_phrases_to_recommendation(self) -> None:
        for content in (
            "麻辣烫和黄焖鸡哪个更值得选？",
            "奶茶想换掉，有什么更好的替代？",
        ):
            with self.subTest(content=content):
                resolved = resolve_message_type(
                    content,
                    profile_id=12,
                    user_id=self.user_id,
                )

                self.assertEqual(resolved, "meal_recommendation")

    def test_resolve_message_type_routes_explanatory_follow_up_to_text(self) -> None:
        resolved = resolve_message_type(
            "为什么拉面通常热量更高？",
            profile_id=12,
            user_id=self.user_id,
        )

        self.assertEqual(resolved, "text")

    def test_resolve_message_type_prefers_text_for_explanatory_follow_up_about_recommendations(self) -> None:
        resolved = resolve_message_type(
            "为什么更推荐烤鸡而不是炸鸡？",
            profile_id=12,
            user_id=self.user_id,
        )

        self.assertEqual(resolved, "text")

    def test_resolve_message_type_routes_explanation_request_about_recommendation_to_text(self) -> None:
        resolved = resolve_message_type(
            "解释一下这个推荐为什么更适合减脂",
            profile_id=12,
            user_id=self.user_id,
        )

        self.assertEqual(resolved, "text")

    def test_resolve_message_type_routes_explanation_request_about_estimate_to_text(self) -> None:
        resolved = resolve_message_type(
            "说明一下这个估算为什么这么高",
            profile_id=12,
            user_id=self.user_id,
        )

        self.assertEqual(resolved, "text")

    def test_resolve_message_type_defaults_plain_meal_descriptions_to_estimate(self) -> None:
        resolved = resolve_message_type(
            "一碗鸡胸肉沙拉加半个牛油果",
            profile_id=12,
            user_id=self.user_id,
        )

        self.assertEqual(resolved, "meal_estimate")

    def test_resolve_message_type_returns_clarification_for_ambiguous_input(self) -> None:
        """不确定输入时返回澄清提问，而非默认估算。"""
        ambiguous_inputs = [
            "帮我看看这顿",
            "吃什么好",
            "吃啥",
            "今天中午吃什么",
        ]
        for content in ambiguous_inputs:
            with self.subTest(content=content):
                resolved = resolve_message_type(
                    content,
                    profile_id=12,
                    user_id=self.user_id,
                )
                self.assertEqual(resolved, "_clarification")

    def test_resolve_message_type_does_not_clarify_when_food_description_present(self) -> None:
        """含食物量词的描述仍走估算，不触发澄清。"""
        resolved = resolve_message_type(
            "一碗面吃什么",
            profile_id=12,
            user_id=self.user_id,
        )
        self.assertEqual(resolved, "meal_estimate")

    def test_resolve_message_type_routes_typical_estimate_question_to_estimate(self) -> None:
        resolved = resolve_message_type(
            "这碗麻辣烫大概有多少蛋白质和碳水？",
            profile_id=12,
            user_id=self.user_id,
        )

        self.assertEqual(resolved, "meal_estimate")

    def test_resolve_message_type_prefers_estimate_for_ambiguous_message_with_estimate_markers(self) -> None:
        resolved = resolve_message_type(
            "汉堡和鸡肉沙拉哪个更适合我今天晚饭？热量大概多少？",
            profile_id=12,
            user_id=self.user_id,
        )

        self.assertEqual(resolved, "meal_estimate")

    def test_send_message_in_session_orchestrates_user_and_assistant_messages(self) -> None:
        session = create_empty_session(self.user_id)

        with patch(
            "backend.services.chat_service.estimate_meal",
            return_value=type(
                "EstimateResultStub",
                (),
                {
                    "title": "Chicken salad",
                    "confidence": "high",
                    "description": "Protein-forward salad with avocado.",
                    "items": [
                        type(
                            "EstimateItemStub",
                            (),
                            {
                                "model_dump": staticmethod(
                                    lambda: {
                                        "name": "Chicken",
                                        "portion": "150g",
                                        "energy": "240 kcal",
                                    }
                                )
                            },
                        )()
                    ],
                    "total_calories": "240 kcal",
                    "suggestion": "A lighter dressing would reduce calories.",
                },
            )(),
        ):
            exchange = send_message_in_session(
                self.user_id,
                int(session["id"]),
                "chicken salad",
                profile_id=12,
            )

        self.assertIsNotNone(exchange)
        self.assertEqual(exchange["session"]["title"], "chicken salad")
        self.assertEqual(exchange["user_message"]["role"], "user")
        self.assertEqual(exchange["assistant_message"]["message_type"], "estimate_result")
        self.assertEqual(exchange["assistant_message"]["result_total"], "240 kcal")

    def test_send_message_in_session_persists_meal_recommendation_message(self) -> None:
        session = create_empty_session(self.user_id)

        with patch(
            "backend.services.chat_service.generate_meal_recommendation",
            return_value=GuidanceReply(
                title="Lighter Dinner Swap",
                description="A higher-protein dinner with less oil.",
                response="可以把炸鸡饭换成烤鸡沙拉，再配一份玉米汤，会更轻一些。",
            ),
        ):
            exchange = send_message_in_session(
                self.user_id,
                int(session["id"]),
                "帮我推荐一个更轻一点的晚餐",
                profile_id=12,
            )

        self.assertIsNotNone(exchange)
        self.assertEqual(exchange["assistant_message"]["message_type"], "meal_recommendation")
        self.assertEqual(
            exchange["assistant_message"]["content"],
            "可以把炸鸡饭换成烤鸡沙拉，再配一份玉米汤，会更轻一些。",
        )
        self.assertIsNone(exchange["assistant_message"]["result_title"])
        self.assertEqual(
            json.loads(exchange["assistant_message"]["payload_json"]),
            {
                "title": "Lighter Dinner Swap",
                "description": "A higher-protein dinner with less oil.",
            },
        )
        self.assertIsNone(exchange["assistant_message"]["result_total"])
        self.assertIsNone(exchange["assistant_message"]["result_items_json"])

    def test_send_message_in_session_uses_recommendation_fallback_message_when_recommendation_fails(self) -> None:
        session = create_empty_session(self.user_id)

        with patch(
            "backend.services.chat_service.generate_meal_recommendation",
            side_effect=RuntimeError("provider unavailable"),
        ):
            exchange = send_message_in_session(
                self.user_id,
                int(session["id"]),
                "帮我推荐一个减脂晚餐",
                profile_id=12,
            )

        self.assertIsNotNone(exchange)
        self.assertEqual(exchange["assistant_message"]["message_type"], "text")
        self.assertEqual(exchange["assistant_message"]["content"], DEFAULT_RECOMMENDATION_ERROR_MESSAGE)

    def test_send_message_in_session_returns_clarification_for_ambiguous_input(self) -> None:
        """不确定输入时返回澄清提问（text 类型），不调用估算或推荐。"""
        exchange = create_session_and_reply(
            self.user_id,
            "帮我看看这顿",
            profile_id=12,
        )
        self.assertIsNotNone(exchange)
        self.assertEqual(exchange["assistant_message"]["message_type"], "text")
        self.assertIn("推荐", exchange["assistant_message"]["content"])
        self.assertIn("估算", exchange["assistant_message"]["content"])
        self.assertEqual(exchange["assistant_message"]["content"], CLARIFICATION_MESSAGE)

    def test_send_message_in_session_persists_text_reply_for_explanatory_follow_up(self) -> None:
        session = create_empty_session(self.user_id)

        with patch(
            "backend.services.chat_service.generate_text_reply",
            return_value=GuidanceReply(
                title="Food Pilot Reply",
                description="A direct explanation.",
                response="拉面通常会同时叠加高油汤底、精制面和叉烧，所以总热量更高。",
            ),
        ):
            exchange = send_message_in_session(
                self.user_id,
                int(session["id"]),
                "为什么拉面通常热量更高？",
                profile_id=12,
            )

        self.assertIsNotNone(exchange)
        self.assertEqual(exchange["assistant_message"]["message_type"], "text")
        self.assertEqual(
            exchange["assistant_message"]["content"],
            "拉面通常会同时叠加高油汤底、精制面和叉烧，所以总热量更高。",
        )
        self.assertEqual(
            json.loads(exchange["assistant_message"]["payload_json"]),
            {
                "text": "拉面通常会同时叠加高油汤底、精制面和叉烧，所以总热量更高。",
            },
        )

    def test_send_message_in_session_uses_text_reply_for_explanation_about_recommendation(self) -> None:
        session = create_empty_session(self.user_id)

        with patch(
            "backend.services.chat_service.generate_text_reply",
            return_value=GuidanceReply(
                title="补充说明",
                description="这是对推荐结果的补充说明。",
                response="更推荐烤鸡，是因为同等份量下它通常油脂更低，也更容易控制总热量。",
            ),
        ):
            exchange = send_message_in_session(
                self.user_id,
                int(session["id"]),
                "解释一下这个推荐为什么更适合减脂",
                profile_id=12,
            )

        self.assertIsNotNone(exchange)
        self.assertEqual(exchange["assistant_message"]["message_type"], "text")
        self.assertEqual(
            exchange["assistant_message"]["content"],
            "更推荐烤鸡，是因为同等份量下它通常油脂更低，也更容易控制总热量。",
        )

    def test_send_message_in_session_persists_fallback_assistant_message_on_estimate_error(self) -> None:
        session = create_empty_session(self.user_id)

        with patch(
            "backend.services.chat_service.estimate_meal",
            side_effect=RuntimeError("provider unavailable"),
        ):
            exchange = send_message_in_session(
                self.user_id,
                int(session["id"]),
                "omelette",
            )

        self.assertIsNotNone(exchange)
        self.assertEqual(exchange["assistant_message"]["message_type"], "text")
        self.assertEqual(exchange["assistant_message"]["content"], DEFAULT_ASSISTANT_ERROR_MESSAGE)

    def test_send_message_in_session_does_not_create_food_log_entries(self) -> None:
        session = create_empty_session(self.user_id)

        with patch(
            "backend.services.chat_service.estimate_meal",
            return_value=type(
                "EstimateResultStub",
                (),
                {
                    "title": "Chicken salad",
                    "confidence": "high",
                    "description": "Protein-forward salad with avocado.",
                    "items": [
                        type(
                            "EstimateItemStub",
                            (),
                            {
                                "model_dump": staticmethod(
                                    lambda: {
                                        "name": "Chicken",
                                        "portion": "150g",
                                        "energy": "240 kcal",
                                    }
                                )
                            },
                        )()
                    ],
                    "total_calories": "240 kcal",
                    "suggestion": "A lighter dressing would reduce calories.",
                },
            )(),
        ):
            exchange = send_message_in_session(
                self.user_id,
                int(session["id"]),
                "chicken salad",
                profile_id=12,
            )

        self.assertIsNotNone(exchange)
        self.assertEqual(exchange["assistant_message"]["message_type"], "estimate_result")

        refreshed = get_session_detail(self.user_id, int(session["id"]))
        self.assertEqual(len(refreshed["messages"]), 2)
        self.assertEqual(refreshed["messages"][1]["message_type"], "estimate_result")

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM food_logs WHERE user_id = ?", (self.user_id,))
            food_log_total = cursor.fetchone()["total"]
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM messages
                WHERE session_id = ? AND message_type = 'estimate_result'
                """,
                (int(session["id"]),),
            )
            result_message_total = cursor.fetchone()["total"]
        finally:
            conn.close()

        self.assertEqual(food_log_total, 0)
        self.assertEqual(result_message_total, 1)

    def test_create_session_and_reply_creates_session_then_persists_reply(self) -> None:
        with patch(
            "backend.services.chat_service.estimate_meal",
            return_value=type(
                "EstimateResultStub",
                (),
                {
                    "title": "Oatmeal bowl",
                    "confidence": "high",
                    "description": "Balanced breakfast with fruit.",
                    "items": [
                        type(
                            "EstimateItemStub",
                            (),
                            {
                                "model_dump": staticmethod(
                                    lambda: {
                                        "name": "Oats",
                                        "portion": "60g",
                                        "energy": "230 kcal",
                                    }
                                )
                            },
                        )()
                    ],
                    "total_calories": "320 kcal",
                    "suggestion": "Add more protein if this is a post-workout meal.",
                },
            )(),
        ):
            exchange = create_session_and_reply(
                self.user_id,
                "oatmeal",
                profile_id=7,
            )

        self.assertEqual(exchange["session"]["title"], "oatmeal")
        self.assertEqual(len(exchange["session"]["messages"]), 2)
        self.assertEqual(exchange["assistant_message"]["message_type"], "estimate_result")

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM food_logs WHERE user_id = ?", (self.user_id,))
            food_log_total = cursor.fetchone()["total"]
        finally:
            conn.close()

        self.assertEqual(food_log_total, 0)

    def test_rename_and_list_sessions_are_user_scoped(self) -> None:
        first = create_empty_session(self.user_id)
        second = create_empty_session(self.user_id)
        append_user_message(
            self.user_id,
            int(first["id"]),
            "older",
            created_at="2026-03-13 09:00:00",
        )
        append_user_message(
            self.user_id,
            int(second["id"]),
            "newer",
            created_at="2026-03-13 10:00:00",
        )

        renamed = rename_session(self.user_id, int(first["id"]), "  custom title  ")
        denied = rename_session(self.other_user_id, int(first["id"]), "nope")
        listed = list_user_sessions(self.user_id)

        self.assertEqual(renamed["title"], "custom title")
        self.assertIsNone(denied)
        self.assertEqual([session["id"] for session in listed], [second["id"], first["id"]])

    def test_delete_session_removes_messages_via_database_cascade(self) -> None:
        detail = create_session_with_first_user_message(self.user_id, "greek yogurt")
        session_id = int(detail["id"])
        append_assistant_message(
            self.user_id,
            session_id,
            content="Estimated at 120 kcal.",
        )

        deleted = delete_session(self.user_id, session_id)
        missing_detail = get_session_detail(self.user_id, session_id)

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) AS total FROM chat_sessions WHERE id = ?", (session_id,))
            session_total = cursor.fetchone()["total"]
            cursor.execute("SELECT COUNT(*) AS total FROM messages WHERE session_id = ?", (session_id,))
            message_total = cursor.fetchone()["total"]
        finally:
            conn.close()

        self.assertTrue(deleted)
        self.assertIsNone(missing_detail)
        self.assertEqual(session_total, 0)
        self.assertEqual(message_total, 0)

    def test_delete_session_preserves_saved_food_log_but_clears_chat_link(self) -> None:
        detail = create_session_with_first_user_message(self.user_id, "greek yogurt")
        session_id = int(detail["id"])
        assistant_result = append_assistant_message(
            self.user_id,
            session_id,
            message_type="estimate_result",
            content="Add berries for fiber.",
            result_title="Greek yogurt",
            result_confidence="high",
            result_description="High-protein snack.",
            result_items_json='[{"name":"Greek yogurt","portion":"1 cup","energy":"120 kcal"}]',
            result_total="120 kcal",
        )
        saved_entry = save_food_log(
            self.user_id,
            "chat_message",
            meal_description="greek yogurt",
            result_title="Greek yogurt",
            result_description="High-protein snack.",
            total_calories="120 kcal",
            ingredients=[
                {
                    "name": "Greek yogurt",
                    "portion": "1 cup",
                    "energy": "120 kcal",
                }
            ],
            session_id=session_id,
            source_message_id=int(assistant_result["id"]),
            result_confidence="high",
            assistant_suggestion="Add berries for fiber.",
        )

        deleted = delete_session(self.user_id, session_id)

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT session_id, source_message_id
                FROM food_logs
                WHERE id = ?
                """,
                (int(saved_entry["id"]),),
            )
            food_log_row = cursor.fetchone()
        finally:
            conn.close()

        self.assertTrue(deleted)
        self.assertIsNotNone(food_log_row)
        self.assertIsNone(food_log_row["session_id"])
        self.assertIsNone(food_log_row["source_message_id"])

    def test_missing_or_foreign_session_returns_none(self) -> None:
        self.assertIsNone(append_user_message(self.user_id, 9999, "missing"))
        self.assertIsNone(append_assistant_message(self.user_id, 9999, content="missing"))
        self.assertIsNone(get_session_detail(self.user_id, 9999))

        detail = create_session_with_first_user_message(self.user_id, "owner only")

        self.assertIsNone(get_session_detail(self.other_user_id, int(detail["id"])))

    def test_invalid_message_payload_bubbles_up_database_error(self) -> None:
        detail = create_session_with_first_user_message(self.user_id, "banana")

        with self.assertRaises(sqlite3.IntegrityError):
            append_assistant_message(
                self.user_id,
                int(detail["id"]),
                message_type="estimate_result",
                result_title="Broken",
                result_confidence="high",
                result_description="Missing required result fields.",
            )


if __name__ == "__main__":
    unittest.main()
