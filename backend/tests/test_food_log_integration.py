import os
import unittest
from unittest.mock import patch

from backend.database.init_db import init_db
from backend.routers.food_log import list_food_log_entries
from backend.schemas.food_log import FoodLogListQuery
from backend.schemas.estimate import EstimateRequest, EstimateResult
from backend.schemas.user import UserCreate
from backend.services.chat_service import create_session_and_reply
from backend.services.estimate_service import create_estimate_response
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
                EstimateRequest(query="oatmeal bowl"),
                self.user.id,
            )

        entries = list_food_log_entries(
            filters=FoodLogListQuery(),
            current_user=self.user,
        )

        self.assertEqual(status_code, 200)
        self.assertTrue(response.success)
        self.assertIsNone(response.food_log_id)
        self.assertEqual(response.save_status, "not_saved")
        self.assertEqual(len(entries), 0)

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
