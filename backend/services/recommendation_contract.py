GUIDANCE_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "description": {"type": "STRING"},
        "response": {"type": "STRING"},
    },
    "required": ["title", "description", "response"],
}


GUIDANCE_RESPONSE_INSTRUCTIONS = {
    "meal_recommendation": """
Return only a JSON object.
Use exactly these top-level keys:
- title
- description
- response
The response should provide a practical recommendation, comparison, swap, or optimization suggestion.
The response must clearly tell the user what to choose, eat, replace, or prioritize.
The description should briefly explain why this direction fits.
Do not output calorie tables, ingredient breakdown arrays, or estimate-style sections.
Do not add markdown, code fences, tables, or extra keys.
""".strip(),
    "text": """
Return only a JSON object.
Use exactly these top-level keys:
- title
- description
- response
The response should answer the user's question directly in a conversational way without calorie tables or ingredient breakdowns.
Do not add markdown, code fences, tables, or extra keys.
""".strip(),
}
