import json
import os
import unittest
from unittest.mock import patch

from backend.database.connection import get_db_connection
from backend.database.init_db import init_db
from backend.schemas.estimate import EstimateResult
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
                    content="grilled chicken and avocado",
                    profile_id=12,
                    message_type=MEAL_ESTIMATE_MESSAGE_TYPE,
                )
        finally:
            conn.close()

        stored_message = get_session_detail(self.user_id, session_id)["messages"][-1]

        self.assertEqual(stored_message["message_type"], "estimate_result")
        self.assertEqual(stored_message["result_title"], "Chicken Avocado Bowl")
        self.assertEqual(stored_message["result_confidence"], "high")
        self.assertEqual(stored_message["result_description"], "High protein with moderate fat.")
        self.assertEqual(stored_message["result_total"], "420 kcal")

        payload = json.loads(stored_message["payload_json"])
        self.assertIn("estimates", payload)
        self.assertEqual(payload["suggestion"], "Use less sauce to reduce calories.")
        self.assertEqual(len(payload["estimates"]), 2)
        self.assertEqual(
            {estimate["total"] for estimate in payload["estimates"]},
            {"240 kcal", "180 kcal"},
        )
        self.assertTrue(all(estimate.get("items") for estimate in payload["estimates"]))

    def test_build_response_by_type_persists_recommendation_contract_fields(self) -> None:
        session = create_empty_session(self.user_id)
        session_id = int(session["id"])

        conn = get_db_connection()
        try:
            with patch(
                "backend.services.chat_service.generate_meal_recommendation",
                return_value=GuidanceReply(
                    title="Dinner recommendation",
                    description="Keep satiety while reducing total fat.",
                    response="Choose grilled chicken salad with pumpkin soup.",
                ),
            ):
                build_response_by_type(
                    conn,
                    self.user_id,
                    session_id,
                    content="recommend a lighter dinner",
                    profile_id=12,
                    message_type=RECOMMENDATION_MESSAGE_TYPE,
                )
        finally:
            conn.close()

        stored_message = get_session_detail(self.user_id, session_id)["messages"][-1]

        self.assertEqual(stored_message["message_type"], "meal_recommendation")
        self.assertEqual(stored_message["content"], "Choose grilled chicken salad with pumpkin soup.")
        self.assertIsNone(stored_message["result_title"])
        self.assertIsNone(stored_message["result_confidence"])
        self.assertIsNone(stored_message["result_description"])
        self.assertIsNone(stored_message["result_items_json"])
        self.assertIsNone(stored_message["result_total"])
        self.assertEqual(
            json.loads(stored_message["payload_json"]),
            {
                "title": "Dinner recommendation",
                "description": "Keep satiety while reducing total fat.",
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
                    title="Follow-up",
                    description="Explain why grilled is preferred.",
                    response="Grilling usually uses less oil than deep frying.",
                ),
            ):
                build_response_by_type(
                    conn,
                    self.user_id,
                    session_id,
                    content="why grilled over fried",
                    profile_id=12,
                    message_type=TEXT_MESSAGE_TYPE,
                )
        finally:
            conn.close()

        stored_message = get_session_detail(self.user_id, session_id)["messages"][-1]

        self.assertEqual(stored_message["message_type"], "text")
        self.assertEqual(stored_message["content"], "Grilling usually uses less oil than deep frying.")
        self.assertEqual(
            json.loads(stored_message["payload_json"]),
            {
                "text": "Grilling usually uses less oil than deep frying.",
            },
        )
        self.assertIsNone(stored_message["result_title"])
        self.assertIsNone(stored_message["result_confidence"])
        self.assertIsNone(stored_message["result_description"])
        self.assertIsNone(stored_message["result_items_json"])
        self.assertIsNone(stored_message["result_total"])


def _build_estimate_result_stub() -> EstimateResult:
    return EstimateResult.model_validate(
        {
            "title": "Chicken Avocado Bowl",
            "confidence": "high",
            "description": "High protein with moderate fat.",
            "items": [
                {
                    "name": "Chicken",
                    "portion": "150g",
                    "energy": "240 kcal",
                    "description": "Lean protein portion.",
                },
                {
                    "name": "Avocado",
                    "portion": "1/2",
                    "energy": "180 kcal",
                    "description": "Healthy fat source.",
                },
            ],
            "totalCalories": "420 kcal",
            "suggestion": "Use less sauce to reduce calories.",
        }
    )


if __name__ == "__main__":
    unittest.main()
