import json
import os
import unittest
from unittest.mock import patch

from backend.database.connection import get_db_connection
from backend.database.init_db import init_db
from backend.routers.insights import insights_analyze, insights_history
from backend.schemas.insights import InsightsAnalyzeData, InsightsAnalyzeRequest
from backend.schemas.user import UserCreate
from backend.services.user_service import create_user


class InsightsHistoryApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = os.path.join(
            os.getcwd(),
            "backend",
            "database",
            "test_insights_history_api.db",
        )
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db_patch = patch("backend.database.connection.db_path", self.db_path)
        self.db_patch.start()
        init_db()

        self.owner = create_user(
            UserCreate.model_validate(
                {
                    "email": "owner-insights@example.com",
                    "passwordHash": "hashed-password",
                    "displayName": "Owner",
                }
            )
        )
        self.peer = create_user(
            UserCreate.model_validate(
                {
                    "email": "peer-insights@example.com",
                    "passwordHash": "hashed-password",
                    "displayName": "Peer",
                }
            )
        )

    def tearDown(self) -> None:
        self.db_patch.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    @patch("backend.routers.insights.analyze_insights")
    def test_reanalyze_overwrites_same_mode_and_date_range(self, mock_analyze_insights) -> None:
        mock_analyze_insights.side_effect = [
            _build_analyze_data(summary="first"),
            _build_analyze_data(summary="second"),
        ]

        first_request = InsightsAnalyzeRequest.model_validate(
            {
                "mode": "day",
                "selectedLogIds": [1, 2],
                "dateRange": {"start": "2026-03-20", "end": "2026-03-20"},
                "cacheKey": "day_2026-03-20_2026-03-20_ids:1-2",
            }
        )
        second_request = InsightsAnalyzeRequest.model_validate(
            {
                "mode": "day",
                "selectedLogIds": [9],
                "dateRange": {"start": "2026-03-20", "end": "2026-03-20"},
                "cacheKey": "day_2026-03-20_2026-03-20_ids:9",
            }
        )

        insights_analyze(body=first_request, current_user=self.owner)
        insights_analyze(body=second_request, current_user=self.owner)

        history = insights_history(current_user=self.owner).model_dump(
            by_alias=True,
            mode="json",
        )
        self.assertEqual(len(history["items"]), 1)
        self.assertEqual(history["items"][0]["mode"], "day")
        self.assertEqual(
            history["items"][0]["dateRange"],
            {"start": "2026-03-20", "end": "2026-03-20"},
        )
        self.assertEqual(
            history["items"][0]["cacheKey"],
            "day_2026-03-20_2026-03-20_ids:9",
        )
        self.assertEqual(history["items"][0]["data"]["ai"]["summary"], "second")

        conn = get_db_connection()
        try:
            count_row = conn.execute(
                """
                SELECT COUNT(*) AS count
                FROM insights_analysis
                WHERE user_id = ?
                AND mode = 'day'
                AND date_start = '2026-03-20'
                AND date_end = '2026-03-20'
                """,
                (self.owner.id,),
            ).fetchone()
            self.assertIsNotNone(count_row)
            self.assertEqual(count_row["count"], 1)

            row = conn.execute(
                """
                SELECT cache_key, selected_log_ids_json, result_json
                FROM insights_analysis
                WHERE user_id = ?
                AND mode = 'day'
                AND date_start = '2026-03-20'
                AND date_end = '2026-03-20'
                """,
                (self.owner.id,),
            ).fetchone()
            self.assertIsNotNone(row)
            self.assertEqual(row["cache_key"], "day_2026-03-20_2026-03-20_ids:9")
            self.assertEqual(json.loads(row["selected_log_ids_json"]), [9])
            self.assertEqual(
                json.loads(row["result_json"])["ai"]["summary"],
                "second",
            )
        finally:
            conn.close()

    @patch("backend.routers.insights.analyze_insights")
    def test_history_is_isolated_by_user_for_same_range(self, mock_analyze_insights) -> None:
        mock_analyze_insights.side_effect = [
            _build_analyze_data(summary="owner"),
            _build_analyze_data(summary="peer"),
        ]
        request = InsightsAnalyzeRequest.model_validate(
            {
                "mode": "week",
                "dateRange": {"start": "2026-03-16", "end": "2026-03-22"},
                "cacheKey": "week_2026-03-16_2026-03-22_all",
            }
        )

        insights_analyze(body=request, current_user=self.owner)
        insights_analyze(body=request, current_user=self.peer)

        owner_history = insights_history(current_user=self.owner).model_dump(
            by_alias=True,
            mode="json",
        )
        peer_history = insights_history(current_user=self.peer).model_dump(
            by_alias=True,
            mode="json",
        )

        self.assertEqual(len(owner_history["items"]), 1)
        self.assertEqual(len(peer_history["items"]), 1)
        self.assertEqual(owner_history["items"][0]["data"]["ai"]["summary"], "owner")
        self.assertEqual(peer_history["items"][0]["data"]["ai"]["summary"], "peer")

    @patch("backend.routers.insights.analyze_insights")
    def test_analyze_without_cache_key_uses_date_range_fallback_key(
        self,
        mock_analyze_insights,
    ) -> None:
        mock_analyze_insights.return_value = _build_analyze_data(summary="fallback")
        request = InsightsAnalyzeRequest.model_validate(
            {
                "mode": "week",
                "dateRange": {"start": "2026-03-16", "end": "2026-03-22"},
            }
        )

        insights_analyze(body=request, current_user=self.owner)

        history = insights_history(current_user=self.owner).model_dump(
            by_alias=True,
            mode="json",
        )
        self.assertEqual(len(history["items"]), 1)
        self.assertEqual(
            history["items"][0]["cacheKey"],
            "week_2026-03-16_2026-03-22",
        )
        self.assertEqual(history["items"][0]["data"]["ai"]["summary"], "fallback")


def _build_analyze_data(summary: str) -> InsightsAnalyzeData:
    return InsightsAnalyzeData.model_validate(
        {
            "aggregation": {
                "total_calories": 1000.0,
                "total_protein": 60.0,
                "total_carbs": 100.0,
                "total_fat": 30.0,
                "protein_ratio": 24.0,
                "carbs_ratio": 40.0,
                "fat_ratio": 36.0,
                "entry_count": 2,
            },
            "entries": [
                {
                    "id": "1",
                    "name": "Meal",
                    "calories": "500 kcal",
                    "date": "Mar 20",
                    "time": "08:00",
                }
            ],
            "ai": {
                "summary": summary,
                "risks": [],
                "actions": ["hydrate"],
            },
        }
    )


if __name__ == "__main__":
    unittest.main()
