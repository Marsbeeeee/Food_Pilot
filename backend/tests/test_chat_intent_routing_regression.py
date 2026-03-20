import unittest

from backend.services.chat_service import resolve_message_type
from backend.tests.fixtures.real_user_intent_regression_cases import (
    REAL_USER_CASES,
)

# 验收标准：高频问题正确分到两大核心意图，错误分流率不超过此阈值
ACCEPTABLE_ERROR_DIVERSION_RATE = 0.00


class ChatIntentRoutingRegressionTests(unittest.TestCase):
    def test_resolve_message_type_keeps_chinese_samples_on_expected_routes(self) -> None:
        cases = [
            ("帮我推荐一个更轻一点的晚餐", "meal_recommendation"),
            ("午饭吃什么比较合适？", "meal_recommendation"),
            ("汉堡和鸡肉沙拉哪个更适合我今天晚饭？", "meal_recommendation"),
            ("鸡胸肉和鸡腿差别是什么，哪个更适合减脂晚餐？", "meal_recommendation"),
            ("炸鸡想换成更健康的，为什么这么换更合适？", "meal_recommendation"),
            ("米饭还是红薯更适合减脂吗？", "meal_recommendation"),
            ("奶茶有没有更健康的平替？", "meal_recommendation"),
            ("为什么更推荐烤鸡而不是炸鸡？", "text"),
            ("为什么这么推荐？", "text"),
            ("解释一下这个推荐为什么更适合减脂", "text"),
            ("说明一下这个估算为什么这么高", "text"),
            ("一碗鸡胸肉沙拉加半个牛油果", "meal_estimate"),
            ("这碗麻辣烫大概有多少蛋白质和碳水？", "meal_estimate"),
            ("汉堡和鸡肉沙拉哪个更适合我今天晚饭？热量大概多少？", "meal_estimate"),
            ("汉堡和沙拉哪个好，卡路里分别是多少？", "meal_estimate"),
            ("  帮我推荐一下   今天晚饭吃什么  ", "meal_recommendation"),
        ]

        for content, expected in cases:
            with self.subTest(content=content):
                resolved = resolve_message_type(
                    content,
                    profile_id=12,
                    user_id=7,
                )

                self.assertEqual(resolved, expected)

    def test_real_user_questions_correctly_routed_to_two_core_intents(self) -> None:
        """小范围验证：真实用户问题回归，推荐像建议、估算像估算。"""
        failures: list[tuple[str, str, str]] = []
        for content, expected in REAL_USER_CASES:
            resolved = resolve_message_type(
                content,
                profile_id=12,
                user_id=7,
            )
            if resolved != expected:
                failures.append((content, expected, resolved))

        total = len(REAL_USER_CASES)
        error_count = len(failures)
        error_rate = error_count / total if total else 0.0

        self.assertLessEqual(
            error_rate,
            ACCEPTABLE_ERROR_DIVERSION_RATE,
            (
                f"错误分流 {error_count}/{total}，错误率 {error_rate:.1%} 超过可接受阈值 {ACCEPTABLE_ERROR_DIVERSION_RATE:.0%}。"
                + (
                    " 误分样本：\n  "
                    + "\n  ".join(
                        f"输入: {c!r} -> 期望 {e}, 实际 {r}"
                        for c, e, r in failures
                    )
                    if failures
                    else ""
                )
            ),
        )


if __name__ == "__main__":
    unittest.main()
