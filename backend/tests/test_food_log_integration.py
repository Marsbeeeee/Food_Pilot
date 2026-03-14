import os
import unittest
from unittest.mock import patch

from backend.database.init_db import init_db
from backend.routers.food_log import (
    list_food_log_entries,
    patch_food_log_entry,
    restore_saved_food_log_entry,
    save_food_log_entry,
    save_food_log_from_estimate_entry,
)
from backend.schemas.food_log import (
    FoodLogFromEstimateRequest,
    FoodLogListQuery,
    FoodLogPatchRequest,
    FoodLogSaveRequest,
)
from backend.schemas.estimate import EstimateRequest, EstimateResult
from backend.schemas.user import UserCreate
from backend.services.chat_service import create_session_and_reply
from backend.services.estimate_service import create_estimate_response
from backend.services.food_log_service import create_food_log, delete_food_log
from backend.services.user_service import create_user


def build_estimate_result(
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


class FoodLogIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = os.path.join(
            os.getcwd(),
            "backend",
            "database",
            "test_food_log_integration.db",
        )
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        self.db_patch = patch("backend.database.connection.db_path", self.db_path)
        self.db_patch.start()
        init_db()

        self.user = create_user(
            UserCreate.model_validate(
                {
                    "email": "owner@example.com",
                    "passwordHash": "hashed-password",
                    "displayName": "Owner",
                }
            )
        )
        self.other_user = create_user(
            UserCreate.model_validate(
                {
                    "email": "other@example.com",
                    "passwordHash": "hashed-password",
                    "displayName": "Other",
                }
            )
        )

    def tearDown(self) -> None:
        self.db_patch.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_new_chat_analysis_does_not_appear_in_food_log_until_saved(self) -> None:
        with patch(
            "backend.services.chat_service.estimate_meal",
            return_value=build_estimate_result(
                title="Chicken Salad",
                description="Protein-forward salad with avocado.",
                total_calories="240 kcal",
                suggestion="A lighter dressing would reduce calories.",
            ),
        ):
            exchange = create_session_and_reply(
                self.user.id,
                "chicken salad",
                profile_id=12,
            )

        entries = list_food_log_entries(
            filters=FoodLogListQuery(),
            current_user=self.user,
        )

        self.assertEqual(len(entries), 0)
        self.assertEqual(exchange["assistant_message"]["message_type"], "estimate_result")

    def test_direct_estimate_does_not_appear_in_food_log_until_saved(self) -> None:
        client_request_id = "estimate-oatmeal-123"
        with patch(
            "backend.services.estimate_service.estimate_meal",
            return_value=build_estimate_result(
                title="Oatmeal Bowl",
                description="Oats with banana and milk.",
                total_calories="320 kcal",
                suggestion="Add nuts if you want more texture.",
            ),
        ):
            status_code, response = create_estimate_response(
                EstimateRequest(
                    query="oatmeal bowl",
                    clientRequestId=client_request_id,
                ),
                self.user.id,
            )

        entries = list_food_log_entries(
            filters=FoodLogListQuery(),
            current_user=self.user,
        )

        self.assertEqual(status_code, 200)
        self.assertTrue(response.success)
        self.assertEqual(response.client_request_id, client_request_id)
        self.assertIsNone(response.food_log_id)
        self.assertEqual(response.save_status, "not_saved")
        self.assertEqual(len(entries), 0)

        first_save = save_food_log_from_estimate_entry(
            request=FoodLogFromEstimateRequest.model_validate(
                {
                    "mealDescription": "oatmeal bowl",
                    "clientRequestId": client_request_id,
                    "estimate": response.data.model_dump(),
                }
            ),
            current_user=self.user,
        )
        second_save = save_food_log_from_estimate_entry(
            request=FoodLogFromEstimateRequest.model_validate(
                {
                    "mealDescription": "oatmeal bowl",
                    "clientRequestId": client_request_id,
                    "estimate": response.data.model_dump(),
                }
            ),
            current_user=self.user,
        )

        saved_entries = list_food_log_entries(
            filters=FoodLogListQuery(),
            current_user=self.user,
        )
        self.assertEqual(first_save.food_log_id, second_save.food_log_id)
        self.assertEqual(len(saved_entries), 1)
        self.assertEqual(saved_entries[0].id, first_save.food_log_id)
        self.assertEqual(saved_entries[0].idempotency_key, f"estimate_api:{client_request_id}")

    def test_repeated_chat_save_requests_return_same_favorite_entry(self) -> None:
        with patch(
            "backend.services.chat_service.estimate_meal",
            return_value=build_estimate_result(
                title="Chicken Salad",
                description="Protein-forward salad with avocado.",
                total_calories="240 kcal",
                suggestion="A lighter dressing would reduce calories.",
            ),
        ):
            exchange = create_session_and_reply(
                self.user.id,
                "chicken salad",
            )

        request_payload = FoodLogSaveRequest.model_validate(
            {
                "sourceType": "chat_message",
                "mealDescription": "chicken salad",
                "resultTitle": "Chicken Salad",
                "resultConfidence": "high",
                "resultDescription": "Protein-forward salad with avocado.",
                "totalCalories": "240 kcal",
                "ingredients": [
                    {
                        "name": "Chicken Salad",
                        "portion": "1 serving",
                        "energy": "240 kcal",
                    }
                ],
                "sessionId": exchange["session"]["id"],
                "sourceMessageId": exchange["assistant_message"]["id"],
                "assistantSuggestion": exchange["assistant_message"]["content"],
            }
        )

        first_save = save_food_log_entry(
            request=request_payload,
            current_user=self.user,
        )
        second_save = save_food_log_entry(
            request=FoodLogSaveRequest.model_validate(request_payload.model_dump(by_alias=True)),
            current_user=self.user,
        )
        saved_entries = list_food_log_entries(
            filters=FoodLogListQuery(),
            current_user=self.user,
        )

        self.assertEqual(first_save.id, second_save.id)
        self.assertEqual(len(saved_entries), 1)
        self.assertEqual(saved_entries[0].id, first_save.id)

    def test_editing_saved_favorite_refreshes_listing_order_and_fields(self) -> None:
        edited_entry = create_food_log(
            self.user.id,
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
            created_at="2000-01-01 08:00:00",
            meal_occurred_at="2000-01-01 07:30:00",
            is_manual=True,
        )
        create_food_log(
            self.user.id,
            "manual",
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
            created_at="2000-01-01 09:00:00",
            meal_occurred_at="2000-01-01 08:45:00",
            is_manual=True,
        )

        patch_food_log_entry(
            int(edited_entry["id"]),
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
                }
            ),
            current_user=self.user,
        )

        refreshed_entries = list_food_log_entries(
            filters=FoodLogListQuery(),
            current_user=self.user,
        )

        self.assertEqual(refreshed_entries[0].id, str(edited_entry["id"]))
        self.assertEqual(refreshed_entries[0].name, "Breakfast Oats Deluxe")
        self.assertEqual(refreshed_entries[0].calories, "260")
        self.assertEqual(len(refreshed_entries[0].breakdown), 2)

    def test_deleted_favorite_can_be_restored_back_into_listing(self) -> None:
        created = create_food_log(
            self.user.id,
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
            created_at="2000-01-01 08:30:00",
            meal_occurred_at="2000-01-01 08:20:00",
            is_manual=True,
        )

        delete_food_log(self.user.id, int(created["id"]))
        entries_after_delete = list_food_log_entries(
            filters=FoodLogListQuery(),
            current_user=self.user,
        )
        restored = restore_saved_food_log_entry(
            int(created["id"]),
            current_user=self.user,
        )
        entries_after_restore = list_food_log_entries(
            filters=FoodLogListQuery(),
            current_user=self.user,
        )

        self.assertEqual(entries_after_delete, [])
        self.assertEqual(restored.id, str(created["id"]))
        self.assertEqual([entry.id for entry in entries_after_restore], [str(created["id"])])

    def test_save_after_delete_reactivates_same_food_log_record(self) -> None:
        with patch(
            "backend.services.chat_service.estimate_meal",
            return_value=build_estimate_result(
                title="Chicken Salad",
                description="Protein-forward salad with avocado.",
                total_calories="240 kcal",
                suggestion="A lighter dressing would reduce calories.",
            ),
        ):
            exchange = create_session_and_reply(
                self.user.id,
                "chicken salad",
            )

        request_payload = FoodLogSaveRequest.model_validate(
            {
                "sourceType": "chat_message",
                "mealDescription": "chicken salad",
                "resultTitle": "Chicken Salad",
                "resultConfidence": "high",
                "resultDescription": "Protein-forward salad with avocado.",
                "totalCalories": "240 kcal",
                "ingredients": [
                    {
                        "name": "Chicken Salad",
                        "portion": "1 serving",
                        "energy": "240 kcal",
                    }
                ],
                "sessionId": exchange["session"]["id"],
                "sourceMessageId": exchange["assistant_message"]["id"],
                "assistantSuggestion": exchange["assistant_message"]["content"],
            }
        )

        first_save = save_food_log_entry(
            request=request_payload,
            current_user=self.user,
        )
        delete_food_log(self.user.id, int(first_save.id))
        second_save = save_food_log_entry(
            request=FoodLogSaveRequest.model_validate(request_payload.model_dump(by_alias=True)),
            current_user=self.user,
        )
        entries = list_food_log_entries(
            filters=FoodLogListQuery(),
            current_user=self.user,
        )

        self.assertEqual(second_save.id, first_save.id)
        self.assertEqual(second_save.status, "active")
        self.assertEqual([entry.id for entry in entries], [first_save.id])

    def test_automatic_analysis_results_do_not_create_food_log_entries_for_any_user(self) -> None:
        with patch(
            "backend.services.chat_service.estimate_meal",
            return_value=build_estimate_result(
                title="Chicken Salad",
                description="Protein-forward salad with avocado.",
                total_calories="240 kcal",
                suggestion="A lighter dressing would reduce calories.",
            ),
        ):
            create_session_and_reply(
                self.user.id,
                "chicken salad",
            )

        with patch(
            "backend.services.estimate_service.estimate_meal",
            return_value=build_estimate_result(
                title="Rice Bowl",
                description="Rice bowl for another account.",
                total_calories="480 kcal",
                suggestion="Reduce sauce to cut calories.",
            ),
        ):
            create_estimate_response(
                EstimateRequest(query="rice bowl"),
                self.other_user.id,
            )

        owner_entries = list_food_log_entries(
            filters=FoodLogListQuery(),
            current_user=self.user,
        )
        other_entries = list_food_log_entries(
            filters=FoodLogListQuery(),
            current_user=self.other_user,
        )

        self.assertEqual(owner_entries, [])
        self.assertEqual(other_entries, [])


if __name__ == "__main__":
    unittest.main()
