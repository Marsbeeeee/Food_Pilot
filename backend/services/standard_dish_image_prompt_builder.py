from dataclasses import dataclass
import re


@dataclass(frozen=True)
class DishPromptExpansionRule:
    category: str
    keywords: tuple[str, ...]
    details: tuple[str, ...]


_FALLBACK_CATEGORY = "generic_food"
_FALLBACK_DETAILS: tuple[str, ...] = (
    "Use a clean bowl or plate with minimal props and clear ingredient boundaries.",
    "Keep texture realistic and avoid adding side dishes not implied by the dish name.",
    "Show natural food volume and color contrast suitable for a product card cover.",
)

_CATEGORY_RULES: tuple[DishPromptExpansionRule, ...] = (
    DishPromptExpansionRule(
        category="stir_fried_noodle",
        keywords=(
            "\u7092\u9762",
            "chowmein",
            "chow mein",
            "friednoodle",
            "fried noodle",
        ),
        details=(
            "Present plate-style stir-fried noodles with visible wok gloss and mixed toppings.",
            "Noodle strands should stay distinct with slight caramelized edges.",
            "Keep the dish dry-style instead of soup-heavy.",
        ),
    ),
    DishPromptExpansionRule(
        category="rice_noodle",
        keywords=(
            "\u7c89",
            "\u7c73\u7c89",
            "\u7c89\u4e1d",
            "\u6cb3\u7c89",
            "\u87ba\u86f3\u7c89",
            "\u9178\u8fa3\u7c89",
            "\u80a0\u7c89",
            "ricenoodle",
            "rice noodle",
            "vermicelli",
            "fen",
        ),
        details=(
            "Use a bowl or shallow bowl with visible rice noodles as the primary structure.",
            "Highlight noodle smoothness and the signature garnish of this dish type.",
            "Preserve authentic plating density instead of oversized garnish-only styling.",
        ),
    ),
    DishPromptExpansionRule(
        category="noodle",
        keywords=(
            "\u9762",
            "\u62c9\u9762",
            "\u62cc\u9762",
            "\u6c64\u9762",
            "noodle",
            "ramen",
            "udon",
            "spaghetti",
        ),
        details=(
            "Serve in a deep bowl with noodles clearly visible as layered strands.",
            "Keep toppings concentrated near center while preserving noodle volume visibility.",
            "For hot dishes, keep a subtle freshly-cooked heat impression.",
        ),
    ),
    DishPromptExpansionRule(
        category="fried_rice",
        keywords=(
            "\u7092\u996d",
            "\u86cb\u7092\u996d",
            "friedrice",
            "fried rice",
        ),
        details=(
            "Present fried rice on a flat plate or shallow bowl with separated grains.",
            "Show mixed ingredients distributed through the rice rather than top-only garnish.",
            "Keep a lightly glossy wok-fried texture without excessive oil shine.",
        ),
    ),
    DishPromptExpansionRule(
        category="rice_bowl",
        keywords=(
            "\u76d6\u996d",
            "\u4e3c",
            "\u996d\u7897",
            "ricebowl",
            "rice bowl",
            "donburi",
        ),
        details=(
            "Use a bowl composition with rice as base and main topping layered on top.",
            "Keep topping-to-rice proportion realistic and clearly readable.",
            "Ensure the top protein or sauce is visually dominant but not spilling over.",
        ),
    ),
    DishPromptExpansionRule(
        category="pizza",
        keywords=(
            "\u62ab\u8428",
            "pizza",
        ),
        details=(
            "Show a round thin-crust pizza with melted cheese and visible topping distribution.",
            "Keep crust edge texture crisp and slightly blistered.",
            "Use a centered full-pie or near full-pie composition suitable for cover usage.",
        ),
    ),
    DishPromptExpansionRule(
        category="burger",
        keywords=(
            "\u6c49\u5821",
            "burger",
            "hamburger",
        ),
        details=(
            "Present one complete burger as the hero object with stacked bun-protein-vegetable layers.",
            "Keep bun texture soft but structured, with realistic height and balance.",
            "Avoid multi-item fast-food combos or side items in frame.",
        ),
    ),
    DishPromptExpansionRule(
        category="salad",
        keywords=(
            "\u6c99\u62c9",
            "salad",
        ),
        details=(
            "Use a clean bowl or plate with fresh leafy base and colorful ingredient contrast.",
            "Keep dressing light and controlled, not fully drowning the ingredients.",
            "Prioritize crisp texture and freshness cues.",
        ),
    ),
    DishPromptExpansionRule(
        category="soup",
        keywords=(
            "\u6c64",
            "soup",
            "broth",
        ),
        details=(
            "Use a bowl composition with clear visible broth surface and floating ingredients.",
            "Keep soup color and density realistic to the named dish.",
            "Avoid over-thick textures unless clearly implied by the dish name.",
        ),
    ),
    DishPromptExpansionRule(
        category="dessert",
        keywords=(
            "\u751c\u54c1",
            "\u86cb\u7cd5",
            "\u5e03\u4e01",
            "\u51b0\u6fc0\u51cc",
            "\u96ea\u7cd5",
            "\u6155\u65af",
            "\u86cb\u631e",
            "\u5976\u51bb",
            "dessert",
            "cake",
            "pudding",
            "icecream",
            "ice cream",
            "mousse",
            "tart",
        ),
        details=(
            "Use refined dessert plating with soft highlights and clean edges.",
            "Keep portion size realistic for a single serving.",
            "Prioritize appealing texture detail, such as cream layers or glaze finish.",
        ),
    ),
    DishPromptExpansionRule(
        category="drink",
        keywords=(
            "\u996e\u54c1",
            "\u5496\u5561",
            "\u5976\u8336",
            "\u679c\u6c41",
            "\u8336",
            "\u6c7d\u6c34",
            "\u6c14\u6ce1",
            "drink",
            "beverage",
            "coffee",
            "latte",
            "milk tea",
            "milktea",
            "tea",
            "juice",
            "smoothie",
        ),
        details=(
            "Use a single cup or glass composition with the beverage as sole hero object.",
            "Keep liquid color, opacity, and foam or garnish details realistic for the drink type.",
            "Avoid additional meals or dessert props in frame.",
        ),
    ),
)


def build_standard_dish_prompt_expansion_section(standard_dish_name: str) -> str:
    normalized_name = standard_dish_name.strip()
    if not normalized_name:
        raise ValueError("standard_dish_name is required")

    category, details = _match_prompt_expansion(normalized_name)
    lines = [
        "Dish-specific details for this dish:",
        f"- Dish category: {category}",
    ]
    lines.extend(f"- {detail}" for detail in details)
    lines.append("- Keep this as a single-dish hero image with no unrelated side items.")
    return "\n".join(lines)


def _match_prompt_expansion(standard_dish_name: str) -> tuple[str, tuple[str, ...]]:
    normalized_name = standard_dish_name.strip().lower()
    compact_name = _normalize_lookup_text(standard_dish_name)
    for rule in _CATEGORY_RULES:
        for keyword in rule.keywords:
            if _keyword_matches(normalized_name, compact_name, keyword):
                return rule.category, rule.details
    return _FALLBACK_CATEGORY, _FALLBACK_DETAILS


def _normalize_lookup_text(value: str) -> str:
    return "".join(value.strip().lower().split())


def _keyword_matches(
    normalized_name: str,
    compact_name: str,
    keyword: str,
) -> bool:
    normalized_keyword = keyword.strip().lower()
    if not normalized_keyword:
        return False

    if _is_ascii_word_keyword(normalized_keyword):
        if " " in normalized_keyword:
            return normalized_keyword in normalized_name
        return bool(re.search(rf"\b{re.escape(normalized_keyword)}\b", normalized_name))

    return _normalize_lookup_text(normalized_keyword) in compact_name


def _is_ascii_word_keyword(value: str) -> bool:
    return all(char.isascii() and (char.isalpha() or char.isspace()) for char in value)
