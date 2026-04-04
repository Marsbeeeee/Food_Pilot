GUIDANCE_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "title": {"type": "STRING"},
        "description": {"type": "STRING"},
        "response": {"type": "STRING"},
    },
    "required": ["title", "description", "response"],
}


GUIDANCE_MODE_RULES = {
    "meal_recommendation": """
Capability boundary:
- This route is only for meal recommendation, comparison, swap, and optimization guidance.
- Give the user a concrete direction first, then a short reason.
- Do not output estimate-style calorie tables, ingredient breakdown arrays, or nutrition card structures.
For comparison questions (e.g. "米饭和红薯哪个更适合减脂期？", "A和B哪个更好？"), directly answer which option fits better and why.
""".strip(),
    "text": """
Capability boundary:
- This route is only for direct textual explanation, small talk, or short clarifications.
- Do not transform this route into a fresh recommendation workflow or a new estimate result.
- Keep the response conversational and concise without estimate-style tables.
""".strip(),
}


GUIDANCE_OUTPUT_CONTRACT = """
Return only a JSON object.
Use exactly these top-level keys:
- title
- description
- response
Do not add markdown, code fences, tables, or extra keys.
""".strip()


GUIDANCE_RESPONSE_INSTRUCTIONS = {
    mode: f"{GUIDANCE_MODE_RULES[mode]}\n\n{GUIDANCE_OUTPUT_CONTRACT}"
    for mode in GUIDANCE_MODE_RULES
}
