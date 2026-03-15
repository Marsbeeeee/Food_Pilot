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
All human-readable values should be written in Simplified Chinese.
Use "高" / "中" / "低" for confidence when possible.
Keep energy and total_calories in a readable format such as "320 kcal".
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
                },
                "required": ["name", "portion", "energy"],
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
