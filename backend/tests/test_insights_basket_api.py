import os
import unittest
from unittest.mock import patch

from pydantic import ValidationError

from backend.database.init_db import init_db
from backend.routers.insights import insights_basket, insights_basket_sync
from backend.schemas.insights import InsightsBasketSyncRequest
from backend.schemas.user import UserCreate
from backend.services.user_service import create_user


class InsightsBasketApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = os.path.join(
            os.getcwd(),
            "backend",
            "database",
            "test_insights_basket_api.db",
        )
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.db_patch = patch("backend.database.connection.db_path", self.db_path)
        self.db_patch.start()
        init_db()

        owner = create_user(
            UserCreate.model_validate(
                {
                    "email": "owner@example.com",
                    "passwordHash": "hashed-password",
                    "displayName": "Owner",
                }
            )
        )
        peer = create_user(
            UserCreate.model_validate(
                {
                    "email": "peer@example.com",
                    "passwordHash": "hashed-password",
                    "displayName": "Peer",
                }
            )
        )
        self.owner = owner
        self.peer = peer

    def tearDown(self) -> None:
        self.db_patch.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_get_returns_empty_basket_when_not_synced(self) -> None:
        response = insights_basket(current_user=self.owner)
        self.assertEqual(_dump_response(response), {"items": []})

    def test_put_and_get_basket_round_trip(self) -> None:
        payload = {
            "items": [
                build_basket_item("basket-a", "2026-03-20", "101", "Oatmeal"),
                build_basket_item("basket-b", "2026-03-20", "102", "Eggs"),
            ]
        }
        request = InsightsBasketSyncRequest.model_validate(payload)

        put_response = insights_basket_sync(body=request, current_user=self.owner)
        self.assertEqual(_dump_response(put_response), payload)

        get_response = insights_basket(current_user=self.owner)
        self.assertEqual(_dump_response(get_response), payload)

    def test_put_replaces_existing_basket_state(self) -> None:
        first_payload = {
            "items": [
                build_basket_item("basket-a", "2026-03-20", "101", "Oatmeal"),
            ]
        }
        second_payload = {"items": []}

        first_request = InsightsBasketSyncRequest.model_validate(first_payload)
        second_request = InsightsBasketSyncRequest.model_validate(second_payload)
        first_response = insights_basket_sync(body=first_request, current_user=self.owner)
        self.assertEqual(_dump_response(first_response), first_payload)

        second_response = insights_basket_sync(body=second_request, current_user=self.owner)
        self.assertEqual(_dump_response(second_response), second_payload)

        get_response = insights_basket(current_user=self.owner)
        self.assertEqual(_dump_response(get_response), second_payload)

    def test_basket_is_isolated_by_user(self) -> None:
        payload = {
            "items": [
                build_basket_item("basket-a", "2026-03-20", "101", "Oatmeal"),
            ]
        }
        request = InsightsBasketSyncRequest.model_validate(payload)

        owner_put = insights_basket_sync(body=request, current_user=self.owner)
        self.assertEqual(_dump_response(owner_put), payload)

        peer_get = insights_basket(current_user=self.peer)
        self.assertEqual(_dump_response(peer_get), {"items": []})

        owner_get = insights_basket(current_user=self.owner)
        self.assertEqual(_dump_response(owner_get), payload)

    def test_put_rejects_invalid_payload(self) -> None:
        with self.assertRaises(ValidationError):
            InsightsBasketSyncRequest.model_validate(
                {
                    "items": [
                        {
                            "analysisDate": "2026-03-20",
                            "snapshot": build_snapshot("101", "Oatmeal"),
                        }
                    ]
                }
            )


def build_basket_item(
    basket_id: str,
    analysis_date: str,
    entry_id: str,
    name: str,
) -> dict[str, object]:
    return {
        "basketId": basket_id,
        "analysisDate": analysis_date,
        "snapshot": build_snapshot(entry_id, name),
    }


def build_snapshot(entry_id: str, name: str) -> dict[str, object]:
    return {
        "id": entry_id,
        "name": name,
        "description": f"{name} description",
        "calories": "320",
        "date": "Mar 20",
        "time": "08:00 AM",
        "savedAt": "2026-03-20 08:00:00",
        "mealOccurredAt": "2026-03-20 08:00:00",
        "status": "active",
        "sourceType": "manual",
        "isManual": True,
        "breakdown": [
            {
                "name": name,
                "portion": "1 bowl",
                "energy": "320 kcal",
            }
        ],
    }


def _dump_response(model) -> dict[str, object]:
    return model.model_dump(by_alias=True, mode="json", exclude_none=True)


if __name__ == "__main__":
    unittest.main()
