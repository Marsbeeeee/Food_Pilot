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
