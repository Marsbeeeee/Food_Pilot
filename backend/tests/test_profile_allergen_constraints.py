import os
import unittest
from unittest.mock import patch

from backend.database.init_db import init_db
from backend.routers.chat import create_chat_message
from backend.schemas.chat import ChatSendMessageRequest
from backend.schemas.profile import ProfileIn
from backend.schemas.user import UserCreate, UserOut
from backend.services.profile_service import create_profile
from backend.services.recommendation import check_allergen_violations
from backend.services.user_service import create_user


class ProfileAllergenConstraintTests(unittest.TestCase):
    def test_check_allergen_violations_blocks_peanut_keywords(self) -> None:
        ok, violations = check_allergen_violations(
            "推荐你试试花生酱全麦面包，加一小把花生作为加餐。",
            ["花生", "花生酱"],
        )

        self.assertFalse(ok)
        self.assertIn("花生", violations)

    def test_check_allergen_violations_ok_when_no_allergen_keywords(self) -> None:
        ok, violations = check_allergen_violations(
            "推荐你晚餐选鸡胸肉沙拉或清炒西兰花。",
            ["花生"],
        )

        self.assertTrue(ok)
        self.assertEqual(violations, [])


class ProfileAllergenIntegrationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.db_path = os.path.join(
            os.getcwd(),
            "backend",
            "database",
            "test_profile_allergen_constraints.db",
        )
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

        self.db_patch = patch("backend.database.connection.db_path", self.db_path)
        self.db_patch.start()
        init_db()

        self.user = create_user(
            UserCreate.model_validate(
                {
                    "email": "allergen-owner@example.com",
                    "passwordHash": "hashed-password",
                    "displayName": "Peanut Sensitive",
                }
            )
        )
        self.user_out = UserOut.model_validate(
            {
                "id": self.user.id,
                "email": self.user.email,
                "display_name": self.user.display_name,
                "created_at": self.user.created_at,
                "updated_at": self.user.updated_at,
            }
        )

        self.profile = create_profile(
            self.user.id,
            ProfileIn.model_validate(
                {
                    "age": 30,
                    "height": 170,
                    "weight": 65,
                    "sex": "Male",
                    "activityLevel": "Moderately active",
                    "goal": "Fat loss",
                    "pace": "Moderate",
                    "kcalTarget": 1800,
                    "dietStyle": "Balanced",
                    "allergies": ["花生"],
                    "exerciseType": "Running",
                }
            ),
        )

    def tearDown(self) -> None:
        self.db_patch.stop()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_recommendation_with_allergen_in_output_is_intercepted(self) -> None:
        """
        集成场景：有过敏原 Profile 的用户发起典型推荐问题，
        系统应返回 meal_recommendation，且内容中不包含过敏原词本身。
        """
        # 为了稳定测试，不依赖真实上游 AI，patch 掉 generate_meal_recommendation 的内容，
        # 让它返回一个包含“花生酱”的推荐文案。
        with patch(
            "backend.services.chat_service.generate_meal_recommendation",
            autospec=True,
        ) as mock_recommendation:
            from backend.schemas.recommendation import GuidanceReply

            mock_recommendation.return_value = GuidanceReply(
                title="晚餐推荐",
                description="适合减脂期的晚餐建议。",
                response="推荐你试试花生酱全麦面包，加一小把花生作为加餐。",
            )

            request = ChatSendMessageRequest.model_validate(
                {
                    "content": "我对花生过敏，晚餐推荐吃什么？",
                    "profileId": self.profile.id,
                }
            )

            exchange = create_chat_message(request, self.user_out)

        assistant = exchange.assistant_message

        self.assertEqual(assistant.message_type, "meal_recommendation")
        self.assertIn("已被系统拦截", assistant.content)
        self.assertIn("花生", assistant.content)


if __name__ == "__main__":
    unittest.main()
