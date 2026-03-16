import unittest

from backend.services.food_log_service import can_save_message_to_food_log


class FoodLogSaveRulesTests(unittest.TestCase):
    def test_can_save_message_to_food_log_accepts_structured_estimate_result(self) -> None:
        message = {
            "message_type": "estimate_result",
            "result_title": "Chicken Salad",
            "result_description": "Protein-forward salad with avocado.",
            "result_items_json": '[{"name":"Chicken","portion":"150g","energy":"240 kcal"}]',
            "result_total": "240 kcal",
        }

        self.assertTrue(can_save_message_to_food_log(message))

    def test_can_save_message_to_food_log_accepts_meal_estimate_alias(self) -> None:
        message = {
            "message_type": "meal_estimate",
            "result_title": "Oatmeal Bowl",
            "result_description": "Oats with banana and milk.",
            "result_items_json": '[{"name":"Oats","portion":"1 bowl","energy":"320 kcal"}]',
            "result_total": "320 kcal",
        }

        self.assertTrue(can_save_message_to_food_log(message))

    def test_can_save_message_to_food_log_rejects_missing_structure(self) -> None:
        missing_items = {
            "message_type": "estimate_result",
            "result_title": "Chicken Salad",
            "result_description": "Protein-forward salad with avocado.",
            "result_items_json": "",
            "result_total": "240 kcal",
        }
        self.assertFalse(can_save_message_to_food_log(missing_items))

        missing_total = {
            "message_type": "estimate_result",
            "result_title": "Chicken Salad",
            "result_description": "Protein-forward salad with avocado.",
            "result_items_json": '[{"name":"Chicken","portion":"150g","energy":"240 kcal"}]',
            "result_total": "",
        }
        self.assertFalse(can_save_message_to_food_log(missing_total))

    def test_can_save_message_to_food_log_rejects_recommendation_and_text(self) -> None:
        recommendation_message = {
            "message_type": "meal_recommendation",
            "result_title": "",
            "result_description": "",
            "result_items_json": "",
            "result_total": "",
        }
        text_message = {
            "message_type": "text",
            "result_title": "",
            "result_description": "",
            "result_items_json": "",
            "result_total": "",
        }

        self.assertFalse(can_save_message_to_food_log(recommendation_message))
        self.assertFalse(can_save_message_to_food_log(text_message))


if __name__ == "__main__":
    unittest.main()

