ESTIMATE_RESPONSE_INSTRUCTION = """
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
All human-readable values should be written in Simplified Chinese.
Use "高" / "中" / "低" for confidence when possible.
Keep energy and total_calories in a readable format such as "320 kcal".
Keep protein, carbs, and fat in a readable format such as "12.5 g".
If a portion is unclear, still provide a short non-empty portion value such as "未说明".
Do not add markdown, code fences, or extra keys.
""".strip()


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
