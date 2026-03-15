import json
import os
import unittest
from unittest.mock import patch

from backend.database.connection import get_db_connection
from backend.database.init_db import init_db
from backend.schemas.recommendation import GuidanceReply
from backend.services.chat_service import (
    MEAL_ESTIMATE_MESSAGE_TYPE,
    RECOMMENDATION_MESSAGE_TYPE,
    TEXT_MESSAGE_TYPE,
    build_response_by_type,
    create_empty_session,
    get_session_detail,
)


class ChatServiceOutputContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = os.path.join(
            os.getcwd(),
            "backend",
            "database",
            "test_chat_service_output_contract.db",
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
                ("contract@example.com", "hashed-password", "Contract User"),
            )
            self.user_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()

    def tearDown(self) -> None:
        self.db_patch.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_build_response_by_type_persists_estimate_contract_fields(self) -> None:
        session = create_empty_session(self.user_id)
        session_id = int(session["id"])

        conn = get_db_connection()
        try:
            with patch(
                "backend.services.chat_service.estimate_meal",
                return_value=_build_estimate_result_stub(),
            ):
                build_response_by_type(
                    conn,
                    self.user_id,
                    session_id,
                    content="一份鸡胸肉沙拉加半个牛油果",
                    profile_id=12,
                    message_type=MEAL_ESTIMATE_MESSAGE_TYPE,
                )
        finally:
            conn.close()

        stored_message = get_session_detail(self.user_id, session_id)["messages"][-1]

        self.assertEqual(stored_message["message_type"], "estimate_result")
        self.assertEqual(stored_message["content"], "这份搭配蛋白质够高，但酱料可以再清淡一点。")
        self.assertEqual(stored_message["result_title"], "鸡胸肉牛油果沙拉")
        self.assertEqual(stored_message["result_confidence"], "high")
        self.assertEqual(stored_message["result_description"], "蛋白质充足，脂肪主要来自牛油果。")
        self.assertEqual(stored_message["result_total"], "420 kcal")
        self.assertEqual(
            json.loads(stored_message["payload_json"]),
            {
                "title": "鸡胸肉牛油果沙拉",
                "confidence": "high",
                "description": "蛋白质充足，脂肪主要来自牛油果。",
                "items": [
                    {
                        "name": "鸡胸肉",
                        "portion": "150g",
                        "energy": "240 kcal",
                    },
                    {
                        "name": "牛油果",
                        "portion": "1/2 个",
                        "energy": "180 kcal",
                    },
                ],
                "total": "420 kcal",
            },
        )

    def test_build_response_by_type_persists_recommendation_contract_fields(self) -> None:
        session = create_empty_session(self.user_id)
        session_id = int(session["id"])

        conn = get_db_connection()
        try:
            with patch(
                "backend.services.chat_service.generate_meal_recommendation",
                return_value=GuidanceReply(
                    title="减脂晚餐建议",
                    description="保留饱腹感，同时减少油脂和精制碳水。",
                    response="今晚优先选鸡肉沙拉，再配一份南瓜汤，会比炸鸡饭更稳妥。",
                ),
            ):
                build_response_by_type(
                    conn,
                    self.user_id,
                    session_id,
                    content="帮我推荐一个更轻一点的晚餐",
                    profile_id=12,
                    message_type=RECOMMENDATION_MESSAGE_TYPE,
                )
        finally:
            conn.close()

        stored_message = get_session_detail(self.user_id, session_id)["messages"][-1]

        self.assertEqual(stored_message["message_type"], "meal_recommendation")
        self.assertEqual(stored_message["content"], "今晚优先选鸡肉沙拉，再配一份南瓜汤，会比炸鸡饭更稳妥。")
        self.assertIsNone(stored_message["result_title"])
        self.assertIsNone(stored_message["result_confidence"])
        self.assertIsNone(stored_message["result_description"])
        self.assertIsNone(stored_message["result_items_json"])
        self.assertIsNone(stored_message["result_total"])
        self.assertEqual(
            json.loads(stored_message["payload_json"]),
            {
                "title": "减脂晚餐建议",
                "description": "保留饱腹感，同时减少油脂和精制碳水。",
            },
        )

    def test_build_response_by_type_persists_text_contract_fields(self) -> None:
        session = create_empty_session(self.user_id)
        session_id = int(session["id"])

        conn = get_db_connection()
        try:
            with patch(
                "backend.services.chat_service.generate_text_reply",
                return_value=GuidanceReply(
                    title="补充说明",
                    description="解释上一次推荐背后的判断逻辑。",
                    response="更推荐烤鸡，是因为同等分量下通常更容易控制油脂和总热量。",
                ),
            ):
                build_response_by_type(
                    conn,
                    self.user_id,
                    session_id,
                    content="为什么更推荐烤鸡而不是炸鸡？",
                    profile_id=12,
                    message_type=TEXT_MESSAGE_TYPE,
                )
        finally:
            conn.close()

        stored_message = get_session_detail(self.user_id, session_id)["messages"][-1]

        self.assertEqual(stored_message["message_type"], "text")
        self.assertEqual(stored_message["content"], "更推荐烤鸡，是因为同等分量下通常更容易控制油脂和总热量。")
        self.assertEqual(
            json.loads(stored_message["payload_json"]),
            {
                "text": "更推荐烤鸡，是因为同等分量下通常更容易控制油脂和总热量。",
            },
        )
        self.assertIsNone(stored_message["result_title"])
        self.assertIsNone(stored_message["result_confidence"])
        self.assertIsNone(stored_message["result_description"])
        self.assertIsNone(stored_message["result_items_json"])
        self.assertIsNone(stored_message["result_total"])


class _EstimateItemStub:
    def __init__(self, name: str, portion: str, energy: str) -> None:
        self.name = name
        self.portion = portion
        self.energy = energy

    def model_dump(self) -> dict[str, str]:
        return {
            "name": self.name,
            "portion": self.portion,
            "energy": self.energy,
        }


class _EstimateResultStub:
    def __init__(self) -> None:
        self.title = "鸡胸肉牛油果沙拉"
        self.confidence = "high"
        self.description = "蛋白质充足，脂肪主要来自牛油果。"
        self.items = [
            _EstimateItemStub("鸡胸肉", "150g", "240 kcal"),
            _EstimateItemStub("牛油果", "1/2 个", "180 kcal"),
        ]
        self.total_calories = "420 kcal"
        self.suggestion = "这份搭配蛋白质够高，但酱料可以再清淡一点。"


def _build_estimate_result_stub() -> _EstimateResultStub:
    return _EstimateResultStub()


if __name__ == "__main__":
    unittest.main()
