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
For comparison questions (e.g. "米饭和红薯哪个更适合减脂期？", "A和B哪个更好？"), directly answer which option fits better and why.
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
Use this mode only for small talk, explanatory follow-ups, or short clarifications about an existing recommendation or estimate.
Do not turn this mode into a fresh recommendation plan, a comparison workflow, or a new estimate result.
Do not add markdown, code fences, tables, or extra keys.
""".strip(),
}
