ESTIMATE_CAPABILITY_RULES = """
Capability boundary:
- This route is only for nutrition estimate output.
- Keep the estimate grounded in the user's described meal and reasonable portion assumptions.
- Do not switch into recommendation-workflow style planning or unrelated explanatory mode.
Interpretation rule for items:
- If the user clearly described multiple dishes or independent foods in one meal, `items` should represent those top-level dishes or foods.
- If the user asked about one single composed dish, `items` should represent the dish's internal components, such as rice, egg, tomato, minced meat, vegetables, sauce, or cooking oil.
- For a single composed dish, keep `title` as the dish name, and make `items` renderable as rows inside one card rather than separate cards.
- Only use multiple top-level dish items when the user truly mentioned multiple dishes or independent foods.
""".strip()


ESTIMATE_OUTPUT_CONTRACT = """
Return only a JSON object.
Use exactly these top-level keys:
- title
- description
- confidence
- items
- total_calories
- suggestion
Each item in items must contain:
- name
- portion
- energy
- protein
- carbs
- fat
- description (optional: brief description of this specific food in Chinese, e.g. "猪肉白菜馅的中式包子，含碳水、蛋白质和适量脂肪")
All human-readable values should be written in Simplified Chinese.
Use "高 / 中 / 低" for confidence when possible.
Keep energy and total_calories in a readable format such as "320 kcal".
Keep protein, carbs, and fat in a readable format such as "12.5 g".
If a portion is unclear, still provide a short non-empty portion value such as "未说明".
Do not add markdown, code fences, or extra keys.
""".strip()


ESTIMATE_RESPONSE_INSTRUCTION = f"{ESTIMATE_CAPABILITY_RULES}\n\n{ESTIMATE_OUTPUT_CONTRACT}"


ESTIMATE_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "description": {"type": "STRING"},
        "confidence": {"type": "STRING"},
        "items": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "name": {"type": "STRING"},
                    "portion": {"type": "STRING"},
                    "energy": {"type": "STRING"},
                    "protein": {"type": "STRING"},
                    "carbs": {"type": "STRING"},
                    "fat": {"type": "STRING"},
                    "description": {"type": "STRING"},
                },
                "required": ["name", "portion", "energy", "protein", "carbs", "fat"],
            },
        },
        "total_calories": {"type": "STRING"},
        "suggestion": {"type": "STRING"},
    },
    "required": [
        "title",
        "description",
        "confidence",
        "items",
        "total_calories",
        "suggestion",
    ],
}
