INSIGHTS_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "summary": {"type": "STRING"},
        "risks": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
        },
        "actions": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
        },
    },
    "required": ["summary", "risks", "actions"],
}


INSIGHTS_SYSTEM_PROMPT = """
You are Food Pilot, a friendly and professional nutrition analyst.
Reply in Simplified Chinese.
You will receive the user's food log aggregation data and entry summaries for a given time range.
Based on the data, provide an honest, practical analysis:
- summary: 2-4 sentences summarizing their eating pattern, calorie level, and macro balance.
- risks: Up to 5 one-sentence risk or deficiency warnings. If there are none, return an empty array.
- actions: 1-5 concrete, actionable improvement suggestions. Be specific (e.g. "午餐增加一份绿叶蔬菜沙拉" instead of "多吃蔬菜").
Return only JSON that matches the requested schema. No markdown, no code fences, no extra keys.
""".strip()
