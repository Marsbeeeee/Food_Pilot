def normalize_food_log_query(value: str) -> str:
    return " ".join(value.strip().split()).casefold()
