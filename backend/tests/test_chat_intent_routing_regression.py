import unittest

from backend.services.chat_service import resolve_message_type


class ChatIntentRoutingRegressionTests(unittest.TestCase):
    def test_resolve_message_type_keeps_chinese_samples_on_expected_routes(self) -> None:
        cases = [
            ("帮我推荐一个更轻一点的晚餐", "meal_recommendation"),
            ("午饭吃什么比较合适？", "meal_recommendation"),
            ("汉堡和鸡肉沙拉哪个更适合我今天晚饭？", "meal_recommendation"),
            ("为什么更推荐烤鸡而不是炸鸡？", "text"),
            ("解释一下这个推荐为什么更适合减脂", "text"),
            ("说明一下这个估算为什么这么高", "text"),
            ("一碗鸡胸肉沙拉加半个牛油果", "meal_estimate"),
            ("这碗麻辣烫大概有多少蛋白质和碳水？", "meal_estimate"),
            ("汉堡和鸡肉沙拉哪个更适合我今天晚饭？热量大概多少？", "meal_estimate"),
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


if __name__ == "__main__":
    unittest.main()
