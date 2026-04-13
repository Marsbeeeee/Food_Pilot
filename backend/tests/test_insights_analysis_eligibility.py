import json
import os
import unittest
from datetime import date
from unittest.mock import patch

from backend.database.init_db import init_db
from backend.schemas.insights import AIInsights
from backend.schemas.user import UserCreate
from backend.services.food_log_service import create_food_log
from backend.services.insights_service import AnalysisEligibilityError, analyze_insights
from backend.services.user_service import create_user


class InsightsAnalysisEligibilityTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = os.path.join(
            os.getcwd(),
            "backend",
            "database",
            "test_insights_analysis_eligibility.db",
        )
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db_patch = patch("backend.database.connection.db_path", self.db_path)
        self.db_patch.start()
        init_db()

        user = create_user(
            UserCreate.model_validate(
                {
                    "email": "insights-owner@example.com",
                    "passwordHash": "hashed-password",
                    "displayName": "Owner",
                }
            )
        )
        self.user_id = user.id

    def tearDown(self) -> None:
        self.db_patch.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_selected_log_ids_reject_analysis_ineligible_entries(self) -> None:
        eligible = self._create_food_log("Eligible Bowl", analysis_eligible=True)
        ineligible = self._create_food_log("Needs Clarification", analysis_eligible=False)

        with self.assertRaises(AnalysisEligibilityError) as exc:
            analyze_insights(
                self.user_id,
                mode="day",
                selected_log_ids=[int(eligible["id"]), int(ineligible["id"])],
                date_start=date(2026, 3, 20),
                date_end=date(2026, 3, 20),
            )

        self.assertIn(str(ineligible["id"]), str(exc.exception))

    @patch(
        "backend.services.insights_service._generate_ai_insights",
        return_value=AIInsights(summary="ok", risks=[], actions=["hydrate"]),
    )
    def test_range_queries_ignore_analysis_ineligible_entries(
        self,
        _mock_generate_ai,
    ) -> None:
        self._create_food_log("Eligible Bowl", analysis_eligible=True)
        self._create_food_log("Needs Clarification", analysis_eligible=False)

        result = analyze_insights(
            self.user_id,
            mode="day",
            selected_log_ids=None,
            date_start=date(2026, 3, 20),
            date_end=date(2026, 3, 20),
        )

        self.assertEqual(result.aggregation.entry_count, 1)
        self.assertEqual(len(result.entries), 1)
        self.assertEqual(result.entries[0].name, "Eligible Bowl")

    def _create_food_log(
        self,
        title: str,
        *,
        analysis_eligible: bool | None,
    ) -> dict[str, object]:
        decision_card_json = None
        if analysis_eligible is not None:
            decision_card_json = json.dumps(
                {"analysisEligible": analysis_eligible},
                ensure_ascii=False,
            )
        return create_food_log(
            self.user_id,
            "estimate_api",
            meal_description=title,
            result_title=title,
            result_description=f"{title} description",
            total_calories="320 kcal",
            ingredients=[
                {
                    "name": title,
                    "portion": "1 bowl",
                    "energy": "320 kcal",
                }
            ],
            decision_card_json=decision_card_json,
            logged_at="2026-03-20 08:00:00",
            created_at="2026-03-20 08:00:00",
        )


if __name__ == "__main__":
    unittest.main()
