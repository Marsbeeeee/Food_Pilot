import json
import os
import unittest
from unittest.mock import patch

from fastapi import HTTPException

from backend.database.init_db import init_db
from backend.routers.food_log import (
    get_food_log_entry,
    list_food_log_entries,
    patch_food_log_entry,
    restore_saved_food_log_entry,
    save_food_log_entry,
    save_food_log_from_estimate_entry,
)
from backend.schemas.estimate import EstimateResult
from backend.schemas.food_log import (
    FoodLogFromEstimateRequest,
    FoodLogListQuery,
    FoodLogPatchRequest,
    FoodLogSaveRequest,
)
from backend.schemas.user import UserCreate
from backend.services.chat_service import create_empty_session
from backend.services.food_log_service import create_food_log, delete_food_log
from backend.services.user_service import create_user


class FoodLogApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = os.path.join(
            os.getcwd(),
            "backend",
            "database",
            "test_food_log_api.db",
        )
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db_patch = patch("backend.database.connection.db_path", self.db_path)
        self.db_patch.start()
        init_db()

        user = create_user(
            UserCreate.model_validate(
                {
                    "email": "owner@example.com",
                    "passwordHash": "hashed-password",
                    "displayName": "Owner",
                }
            )
        )
        self.user = user
        self.user_id = user.id
        other_user = create_user(
            UserCreate.model_validate(
                {
                    "email": "other@example.com",
                    "passwordHash": "hashed-password",
                    "displayName": "Other",
                }
            )
        )
        self.other_user_id = other_user.id

    def tearDown(self) -> None:
        self.db_patch.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_food_logs_returns_explorer_ready_fields(self) -> None:
        session = create_empty_session(self.user_id)
        create_food_log(
            self.user_id,
            "chat_message",
            meal_description="chicken salad",
            result_title="Chicken Salad",
            result_description="Protein-forward salad with avocado.",
            total_calories="240 kcal",
            ingredients=[
                {
                    "name": "Chicken",
                    "portion": "150g",
                    "energy": "240 kcal",
                }
            ],
            session_id=int(session["id"]),
            logged_at="2026-03-14 08:15:00",
            created_at="2026-03-14 08:15:00",
        )
        create_food_log(
            self.user_id,
            "estimate_api",
            meal_description="oatmeal bowl",
            result_title="Oatmeal Bowl",
            result_description="Oats with banana and milk.",
            total_calories="320 kcal",
            ingredients=[
                {
                    "name": "Oats",
                    "portion": "1 bowl",
                    "energy": "320 kcal",
                }
            ],
            logged_at="2026-03-14 09:30:00",
            created_at="2026-03-14 09:30:00",
        )

        entries = list_food_log_entries(
            filters=FoodLogListQuery(),
            current_user=self.user,
        )
        payload = [entry.model_dump(by_alias=True, exclude_none=True) for entry in entries]

        self.assertEqual(len(payload), 2)

        latest_entry = payload[0]
        self.assertEqual(
            latest_entry,
            {
                "id": latest_entry["id"],
                "name": "Oatmeal Bowl",
                "description": "Oats with banana and milk.",
                "calories": "320",
                "date": "Mar 14",
                "time": "09:30 AM",
                "savedAt": "2026-03-14 09:30:00",
                "mealOccurredAt": "2026-03-14 09:30:00",
                "status": "active",
                "sourceType": "estimate_api",
                "isManual": False,
                "breakdown": [
                    {
                        "name": "Oats",
                        "portion": "1 bowl",
                        "energy": "320 kcal",
                    }
                ],
            },
        )
        self.assertNotIn("sessionId", latest_entry)
        self.assertNotIn("image", latest_entry)
        self.assertNotIn("protein", latest_entry)
        self.assertNotIn("carbs", latest_entry)
        self.assertNotIn("fat", latest_entry)

        linked_entry = payload[1]
        self.assertEqual(linked_entry["name"], "Chicken Salad")
        self.assertEqual(linked_entry["calories"], "240")
        self.assertEqual(linked_entry["date"], "Mar 14")
        self.assertEqual(linked_entry["time"], "08:15 AM")
        self.assertEqual(linked_entry["savedAt"], "2026-03-14 08:15:00")
        self.assertEqual(linked_entry["mealOccurredAt"], "2026-03-14 08:15:00")
        self.assertEqual(linked_entry["sessionId"], str(session["id"]))
        self.assertEqual(linked_entry["status"], "active")
        self.assertEqual(linked_entry["sourceType"], "chat_message")
        self.assertFalse(linked_entry["isManual"])

    def test_get_food_logs_supports_session_limit_date_query_sort_source_and_image_filters(self) -> None:
        lunch_session = create_empty_session(self.user_id)
        dinner_session = create_empty_session(self.user_id)

        create_food_log(
            self.user_id,
            "chat_message",
            meal_description="chicken salad with avocado",
            result_title="Chicken Salad",
            result_description="Lunch salad.",
            total_calories="240 kcal",
            ingredients=[
                {
                    "name": "Chicken",
                    "portion": "150g",
                    "energy": "240 kcal",
                }
            ],
            session_id=int(lunch_session["id"]),
            logged_at="2026-03-13 12:00:00",
            created_at="2026-03-13 12:00:00",
        )
        create_food_log(
            self.user_id,
            "chat_message",
            meal_description="salmon rice bowl",
            result_title="Salmon Bowl",
            result_description="Dinner bowl.",
            total_calories="520 kcal",
            ingredients=[
                {
                    "name": "Salmon",
                    "portion": "180g",
                    "energy": "520 kcal",
                }
            ],
            session_id=int(dinner_session["id"]),
            image="https://img.example/salmon.jpg",
            logged_at="2026-03-14 18:30:00",
            created_at="2026-03-14 18:30:00",
        )
        create_food_log(
            self.user_id,
            "estimate_api",
            meal_description="oatmeal breakfast",
            result_title="Oatmeal Bowl",
            result_description="Breakfast oats.",
            total_calories="320 kcal",
            ingredients=[
                {
                    "name": "Oats",
                    "portion": "1 bowl",
                    "energy": "320 kcal",
                }
            ],
            logged_at="2026-03-15 08:00:00",
            created_at="2026-03-15 08:00:00",
        )
        create_food_log(
            self.other_user_id,
            "estimate_api",
            meal_description="salad owned by another user",
            result_title="Other User Salad",
            result_description="Should not be visible.",
            total_calories="410 kcal",
            ingredients=[
                {
                    "name": "Lettuce",
                    "portion": "1 bowl",
                    "energy": "410 kcal",
                }
            ],
            logged_at="2026-03-15 09:00:00",
            created_at="2026-03-15 09:00:00",
        )

        lunch_entries = list_food_log_entries(
            filters=FoodLogListQuery.model_validate(
                {
                    "sessionId": int(lunch_session["id"]),
                }
            ),
            current_user=self.user,
        )
        self.assertEqual([entry.name for entry in lunch_entries], ["Chicken Salad"])

        ranged_entries = list_food_log_entries(
            filters=FoodLogListQuery.model_validate(
                {
                    "dateFrom": "2026-03-14",
                    "dateTo": "2026-03-15",
                    "limit": 2,
                }
            ),
            current_user=self.user,
        )
        self.assertEqual([entry.name for entry in ranged_entries], ["Oatmeal Bowl", "Salmon Bowl"])

        query_entries = list_food_log_entries(
            filters=FoodLogListQuery.model_validate(
                {
                    "query": "salad",
                }
            ),
            current_user=self.user,
        )
        self.assertEqual([entry.name for entry in query_entries], ["Chicken Salad"])

        legacy_meal_entries = list_food_log_entries(
            filters=FoodLogListQuery.model_validate(
                {
                    "meal": "salad",
                }
            ),
            current_user=self.user,
        )
        self.assertEqual([entry.name for entry in legacy_meal_entries], ["Chicken Salad"])

        asc_sorted_entries = list_food_log_entries(
            filters=FoodLogListQuery.model_validate(
                {
                    "dateFrom": "2026-03-14",
                    "dateTo": "2026-03-15",
                    "sort": "created_asc",
                }
            ),
            current_user=self.user,
        )
        self.assertEqual([entry.name for entry in asc_sorted_entries], ["Salmon Bowl", "Oatmeal Bowl"])

        estimate_api_entries = list_food_log_entries(
            filters=FoodLogListQuery.model_validate(
                {
                    "sourceType": "estimate_api",
                }
            ),
            current_user=self.user,
        )
        self.assertEqual([entry.name for entry in estimate_api_entries], ["Oatmeal Bowl"])

        with_image_entries = list_food_log_entries(
            filters=FoodLogListQuery.model_validate(
                {
                    "hasImage": True,
                }
            ),
            current_user=self.user,
        )
        self.assertEqual([entry.name for entry in with_image_entries], ["Salmon Bowl"])

        combined_entries = list_food_log_entries(
            filters=FoodLogListQuery.model_validate(
                {
                    "query": "salmon",
                    "sourceType": "chat_message",
                    "hasImage": True,
                    "dateFrom": "2026-03-14",
                    "dateTo": "2026-03-14",
                    "sort": "created_desc",
                }
            ),
            current_user=self.user,
        )
        self.assertEqual([entry.name for entry in combined_entries], ["Salmon Bowl"])

    def test_get_food_log_entry_returns_single_entry(self) -> None:
        created = create_food_log(
            self.user_id,
            "manual",
            meal_description="greek yogurt bowl",
            result_title="Greek Yogurt Bowl",
            result_description="Yogurt with fruit.",
            total_calories="280 kcal",
            ingredients=[
                {
                    "name": "Greek yogurt",
                    "portion": "1 bowl",
                    "energy": "280 kcal",
                }
            ],
            meal_occurred_at="2026-03-14 08:20:00",
            created_at="2026-03-14 08:30:00",
            is_manual=True,
        )

        response = get_food_log_entry(int(created["id"]), current_user=self.user)

        payload = response.model_dump(by_alias=True, exclude_none=True)
        self.assertEqual(payload["id"], str(created["id"]))
        self.assertEqual(payload["name"], "Greek Yogurt Bowl")
        self.assertEqual(payload["sourceType"], "manual")
        self.assertTrue(payload["isManual"])

    def test_patch_food_log_entry_updates_existing_record(self) -> None:
        created = create_food_log(
            self.user_id,
            "manual",
            meal_description="breakfast oats",
            result_title="Breakfast Oats",
            result_description="Original description",
            total_calories="240 kcal",
            ingredients=[
                {
                    "name": "Oats",
                    "portion": "1 bowl",
                    "energy": "240 kcal",
                }
            ],
            meal_occurred_at="2026-03-14 07:30:00",
            created_at="2026-03-14 08:00:00",
            is_manual=True,
        )

        response = patch_food_log_entry(
            int(created["id"]),
            request=FoodLogPatchRequest.model_validate(
                {
                    "resultTitle": "Breakfast Oats Deluxe",
                    "resultDescription": "Updated description",
                    "totalCalories": "260 kcal",
                    "ingredients": [
                        {
                            "name": "Oats",
                            "portion": "1 bowl",
                            "energy": "220 kcal",
                        },
                        {
                            "name": "Blueberries",
                            "portion": "50g",
                            "energy": "40 kcal",
                        },
                    ],
                    "mealOccurredAt": "2026-03-14 07:45:00",
                }
            ),
            current_user=self.user,
        )

        payload = response.model_dump(by_alias=True, exclude_none=True)
        self.assertEqual(payload["name"], "Breakfast Oats Deluxe")
        self.assertEqual(payload["description"], "Updated description")
        self.assertEqual(payload["calories"], "260")
        self.assertEqual(payload["mealOccurredAt"], "2026-03-14 07:45:00")
        self.assertEqual(len(payload["breakdown"]), 2)

    def test_restore_saved_food_log_entry_reactivates_deleted_record(self) -> None:
        created = create_food_log(
            self.user_id,
            "estimate_api",
            meal_description="salmon bowl",
            result_title="Salmon Bowl",
            result_description="Fresh salmon bowl.",
            total_calories="520 kcal",
            ingredients=[
                {
                    "name": "Salmon",
                    "portion": "180g",
                    "energy": "520 kcal",
                }
            ],
            created_at="2026-03-14 09:00:00",
        )
        delete_food_log(self.user_id, int(created["id"]))

        response = restore_saved_food_log_entry(
            int(created["id"]),
            current_user=self.user,
        )

        payload = response.model_dump(by_alias=True, exclude_none=True)
        self.assertEqual(payload["id"], str(created["id"]))
        self.assertEqual(payload["status"], "active")

        entries = list_food_log_entries(
            filters=FoodLogListQuery(),
            current_user=self.user,
        )
        self.assertEqual([entry.id for entry in entries], [str(created["id"])])

    def test_save_food_log_from_estimate_returns_saved_metadata(self) -> None:
        request = FoodLogFromEstimateRequest.model_validate(
            {
                "mealDescription": "oatmeal bowl",
                "clientRequestId": "estimate-123",
                "estimate": _build_estimate_result(
                    title="Oatmeal Bowl",
                    description="Oats with banana and milk.",
                    total_calories="320 kcal",
                    suggestion="Add nuts for more texture.",
                ).model_dump(),
                "mealOccurredAt": "2026-03-14 09:30:00",
            }
        )

        response = save_food_log_from_estimate_entry(
            request=request,
            current_user=self.user,
        )
        duplicate_response = save_food_log_from_estimate_entry(
            request=FoodLogFromEstimateRequest.model_validate(
                request.model_dump(by_alias=True)
            ),
            current_user=self.user,
        )

        payload = response.model_dump(by_alias=True, exclude_none=True)
        duplicate_payload = duplicate_response.model_dump(by_alias=True, exclude_none=True)
        self.assertEqual(payload["clientRequestId"], "estimate-123")
        self.assertEqual(payload["saveStatus"], "saved")
        self.assertEqual(payload["foodLog"]["sourceType"], "estimate_api")
        self.assertEqual(payload["foodLog"]["idempotencyKey"], "estimate_api:estimate-123")
        self.assertEqual(payload["foodLog"]["mealOccurredAt"], "2026-03-14 09:30:00")
        self.assertEqual(payload["foodLogId"], payload["foodLog"]["id"])
        self.assertEqual(duplicate_payload["foodLogId"], payload["foodLogId"])

        entries = list_food_log_entries(
            filters=FoodLogListQuery(),
            current_user=self.user,
        )
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0].id, payload["foodLogId"])

    def test_save_food_log_entry_with_image_defaults_audit_fields(self) -> None:
        request = FoodLogSaveRequest.model_validate(
            {
                "sourceType": "manual",
                "mealDescription": "beef bowl",
                "resultTitle": "Beef Bowl",
                "resultDescription": "Manual image save.",
                "totalCalories": "430 kcal",
                "ingredients": [],
                "image": " https://img.example/beef.jpg ",
                "isManual": True,
            }
        )

        response = save_food_log_entry(
            request=request,
            current_user=self.user,
        )
        payload = response.model_dump(by_alias=True, exclude_none=True)

        self.assertEqual(payload["image"], "https://img.example/beef.jpg")
        self.assertEqual(payload["imageSource"], "manual")
        self.assertEqual(payload["imageLicense"], "user_owned")

    def test_save_food_log_entry_rejects_image_metadata_without_image(self) -> None:
        request = FoodLogSaveRequest.model_validate(
            {
                "sourceType": "manual",
                "mealDescription": "beef bowl",
                "resultTitle": "Beef Bowl",
                "resultDescription": "Invalid image metadata.",
                "totalCalories": "430 kcal",
                "ingredients": [],
                "imageSource": "manual",
                "imageLicense": "user_owned",
                "isManual": True,
            }
        )

        with self.assertRaises(HTTPException) as exc:
            save_food_log_entry(
                request=request,
                current_user=self.user,
            )

        self.assertEqual(exc.exception.status_code, 400)
        self.assertIn("require image", str(exc.exception.detail))

    def test_patch_food_log_entry_clears_image_metadata_when_image_is_empty(self) -> None:
        created = create_food_log(
            self.user_id,
            "manual",
            meal_description="beef bowl",
            result_title="Beef Bowl",
            result_description="Manual image save.",
            total_calories="430 kcal",
            ingredients=[],
            image="https://img.example/beef.jpg",
            image_source="manual",
            image_license="user_owned",
            is_manual=True,
        )

        response = patch_food_log_entry(
            int(created["id"]),
            request=FoodLogPatchRequest.model_validate(
                {
                    "image": "",
                }
            ),
            current_user=self.user,
        )
        payload = response.model_dump(by_alias=True, exclude_none=True)

        self.assertNotIn("image", payload)
        self.assertNotIn("imageSource", payload)
        self.assertNotIn("imageLicense", payload)

    def test_save_food_log_from_estimate_with_image_defaults_audit_fields(self) -> None:
        request = FoodLogFromEstimateRequest.model_validate(
            {
                "mealDescription": "oatmeal bowl",
                "clientRequestId": "estimate-with-image",
                "estimate": _build_estimate_result(
                    title="Oatmeal Bowl",
                    description="Oats with banana and milk.",
                    total_calories="320 kcal",
                    suggestion="Add nuts for more texture.",
                ).model_dump(),
                "image": "https://img.example/oatmeal.jpg",
                "mealOccurredAt": "2026-03-14 09:30:00",
            }
        )

        response = save_food_log_from_estimate_entry(
            request=request,
            current_user=self.user,
        )
        payload = response.model_dump(by_alias=True, exclude_none=True)

        self.assertEqual(payload["foodLog"]["image"], "https://img.example/oatmeal.jpg")
        self.assertEqual(payload["foodLog"]["imageSource"], "estimate_api")
        self.assertEqual(payload["foodLog"]["imageLicense"], "user_owned")

    def test_save_food_log_entry_from_chat_estimate_succeeds(self) -> None:
        """
        chat 鈫?Food Log锛氬浜?estimate 缁撴灉锛堢粨鏋勫畬鏁达級锛屼繚瀛樺簲鎴愬姛銆?        """
        session = create_empty_session(self.user_id)
        from backend.database.connection import get_db_connection

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO messages (
                    session_id,
                    user_id,
                    role,
                    message_type,
                    content,
                    result_title,
                    result_confidence,
                    result_description,
                    result_items_json,
                    result_total,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(session["id"]),
                    self.user_id,
                    "assistant",
                    "estimate_result",
                    "A lighter dressing would reduce calories.",
                    "Chicken Salad",
                    "high",
                    "Protein-forward salad with avocado.",
                    '[{"name":"Chicken","portion":"150g","energy":"240 kcal"}]',
                    "240 kcal",
                    "2026-03-16 12:00:00",
                ),
            )
            message_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()

        request = FoodLogSaveRequest.model_validate(
            {
                "sourceType": "chat_message",
                "mealDescription": "chicken salad",
                "resultTitle": "Chicken Salad",
                "resultDescription": "Protein-forward salad with avocado.",
                "totalCalories": "240 kcal",
                "ingredients": [
                    {
                        "name": "Chicken",
                        "portion": "150g",
                        "energy": "240 kcal",
                    }
                ],
                "sessionId": int(session["id"]),
                "sourceMessageId": int(message_id),
            }
        )

        entry = save_food_log_entry(
            request=request,
            current_user=self.user,
        )

        payload = entry.model_dump(by_alias=True, exclude_none=True)
        self.assertEqual(payload["name"], "Chicken Salad")
        self.assertEqual(payload["sourceType"], "chat_message")

    def test_save_food_log_entry_from_chat_recommendation_is_rejected(self) -> None:
        """
        chat -> Food Log: recommendation replies should not be savable.
        """
        session = create_empty_session(self.user_id)
        from backend.database.connection import get_db_connection

        conn = get_db_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT INTO messages (
                    session_id,
                    user_id,
                    role,
                    message_type,
                    content,
                    payload_json,
                    created_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    int(session["id"]),
                    self.user_id,
                    "assistant",
                    "meal_recommendation",
                    "General healthy eating advice.",
                    json.dumps(
                        {
                            "title": "General advice",
                            "description": "Eat more vegetables and reduce oil/salt.",
                        },
                        ensure_ascii=False,
                    ),
                    "2026-03-16 12:10:00",
                ),
            )
            message_id = cursor.lastrowid
            conn.commit()
        finally:
            conn.close()

        request = FoodLogSaveRequest.model_validate(
            {
                "sourceType": "chat_message",
                "mealDescription": "generic advice",
                "resultTitle": "General advice",
                "resultDescription": "Eat more vegetables and reduce oil/salt.",
                "totalCalories": "0 kcal",
                "ingredients": [],
                "sessionId": int(session["id"]),
                "sourceMessageId": int(message_id),
            }
        )

        with self.assertRaises(Exception) as exc:
            save_food_log_entry(
                request=request,
                current_user=self.user,
            )

        self.assertIn("assistant estimate result", str(exc.exception))

def _build_estimate_result(
    *,
    title: str,
    description: str,
    total_calories: str,
    suggestion: str,
) -> EstimateResult:
    return EstimateResult(
        title=title,
        description=description,
        confidence="high",
        items=[
            {
                "name": title,
                "portion": "1 serving",
                "energy": total_calories,
            }
        ],
        total_calories=total_calories,
        suggestion=suggestion,
    )


if __name__ == "__main__":
    unittest.main()

