import json

import re

from backend.database.connection import get_db_connection
from backend.schemas.decision_card import (
    build_clarification_decision_card,
    build_decision_card_from_estimate,
)
from backend.repositories.chat_session_repository import (
    create_session as create_session_record,
    delete_session as delete_session_record,
    get_session_by_id as get_session_by_id_record,
    list_sessions_by_user as list_sessions_by_user_record,
    update_session_title as update_session_title_record,
)
from backend.repositories.message_repository import (
    create_message as create_message_record,
    list_messages_by_session as list_messages_by_session_record,
)
from backend.services.estimate_parser import split_estimate_by_items
from backend.services.food_knowledge import query_needs_standard_dish_clarification
from backend.services.recommendation import (
    generate_meal_recommendation,
    generate_text_reply,
    check_allergen_violations,
)
from backend.services.profile_service import get_profile


DEFAULT_SESSION_TITLE = "新对话"
MAX_SESSION_TITLE_LENGTH = 120
DEFAULT_ESTIMATE_ERROR_MESSAGE = "这次估算暂时没有完成，请稍后重试，或补充更具体的餐食描述。"
DEFAULT_RECOMMENDATION_ERROR_MESSAGE = "这次推荐暂时没有完成，请稍后重试，或换一种更明确的问法。"
DEFAULT_TEXT_ERROR_MESSAGE = "这次回复暂时没有完成，请稍后重试。"
DEFAULT_ASSISTANT_ERROR_MESSAGE = DEFAULT_ESTIMATE_ERROR_MESSAGE
DEFAULT_RESOLVED_MESSAGE_TYPE = "meal_estimate"
RECOMMENDATION_MESSAGE_TYPE = "meal_recommendation"
TEXT_MESSAGE_TYPE = "text"
MEAL_ESTIMATE_MESSAGE_TYPE = "meal_estimate"
CLARIFICATION_NEEDED = "_clarification"
DEFAULT_CHAT_INPUT_MODE = "chat"
DECISION_CHAT_INPUT_MODE = "decision"
RECOMMENDATION_ROUTE_PHRASES = (
    "推荐",  # 单独「推荐」即可触发，覆盖「推荐训练后吃什么」「推荐减脂晚餐」等
    "推荐吃什么",
    "推荐一个",
    "推荐一下",
    "适合吃什么",
    "训练后吃什么",
    "吃什么比较合适",
    "吃什么更合适",
    "午饭吃什么",
    "晚饭吃什么",
    "午餐吃什么",
    "晚餐吃什么",
    "早餐吃什么",
    "宵夜吃什么",
    "夜宵吃什么",
    "帮我选",
    "怎么选",
    "选哪个",
    "哪个好",
    "哪个更好",
    "哪个更适合",
    "对比一下",
    "比较一下",
    "换什么",
    "换成什么",
    "替代方案",
    "有什么替代",
    "怎么优化",
    "优化一下",
    "套餐怎么选",
    "套餐选哪个",
)
ESTIMATE_ROUTE_PHRASES = (
    "多少热量",
    "多少卡",
    "多少千卡",
    "多少大卡",
    "多少蛋白质",
    "多少碳水",
    "多少脂肪",
    "大概多少",
    "热量大概",
    "营养大概",
    "营养怎么样",
    "营养结构",
)
NUTRITION_TOPIC_PHRASES = (
    "热量",
    "卡路里",
    "千卡",
    "大卡",
    "蛋白质",
    "碳水",
    "脂肪",
    "营养",
    "能量",
)
NUTRITION_QUANTITY_PHRASES = (
    "多少",
    "是多少",
    "几克",
    "几千卡",
    "几大卡",
    "几卡",
    "几卡路里",
    "有多高",
    "有多低",
)
TEXT_ROUTE_PHRASES = (
    "你好",
    "谢谢",
    "为什么",
    "为啥",
    "解释一下",
    "解释下",
    "解释",
    "区别",
    "差别",
    "原理",
    "怎么理解",
    "展开讲",
    "什么意思",
    "说明一下",
    "详细说说",
    "详细讲讲",
    "看不懂",
)
# 当输入既无推荐关键词也无估算关键词，且包含以下模糊表述时，触发澄清提问
AMBIGUOUS_PHRASES = (
    "吃什么",
    "吃什么好",
    "吃啥",
    "吃点什么",
    "帮我看看",
    "看看这顿",
    "这顿怎么样",
)
# 澄清提问的固定回复
CLARIFICATION_MESSAGE = (
    "您是想让我推荐餐食，还是想估算已吃的食物营养？\n\n"
    "· 推荐：告诉我你的需求（如「减脂晚餐」「训练后吃什么」），我会给出建议；\n"
    "· 估算：描述你已吃的食物（如「一碗牛肉面」「两个包子一杯豆浆」），我会帮你算热量和营养。"
)
PRODUCT_DETAIL_CLARIFICATION_MESSAGE = (
    "这个描述还不够具体，我暂时不能稳定判断是哪一款商品。\n\n"
    "请补充更具体的信息，例如：\n"
    "· 具体品名：如「板烧鸡腿堡」「双层吉士汉堡」\n"
    "· 规格或选项：如「大杯」「三分糖」「加芝士」\n"
    "· 套餐构成：如是否带薯条、可乐或其他配餐"
)
DECISION_PRODUCT_SUBJECT_CLARIFICATION_MESSAGE = (
    "我还没看到明确的商品主体，暂时不能进入稳定决策。\n\n"
    "请补充更具体的信息，例如：\n"
    "· 商品名：如「生椰拿铁」「板烧鸡腿堡」\n"
    "· 规格或选项：如「大杯」「三分糖」「少冰」\n"
    "· 套餐内容：如「汉堡 + 薯条 + 可乐」"
)
# 食物描述常见量词，用于区分「模糊提问」与「食物描述」
FOOD_QUANTITY_PATTERNS = (
    "一碗", "两碗", "一份", "两份", "一杯", "两杯",
    "一个", "两个", "半个", "一根", "两根",
)
AMBIGUOUS_STANDARD_DISH_ESTIMATE_HINTS = (
    "热量",
    "营养",
    "卡路里",
    "千卡",
    "大卡",
    "能量",
    "蛋白质",
    "碳水",
    "脂肪",
    "多少卡",
    "多少热量",
    "多少",
)
GENERIC_AMBIGUOUS_DISH_PREFIXES = (
    "一份",
    "一个",
    "这份",
    "那个",
    "这个",
    "这种",
    "那种",
)
ADDITIONAL_RECOMMENDATION_ROUTE_PHRASES = (
    "更值得选",
    "换掉",
    "更好的替代",
    "替代",
    "平替",
    "替换成",
    "替换",
    "换成更健康",
    "更健康的替代",
)
EXPLANATORY_FOLLOW_UP_PHRASES = (
    "这个推荐",
    "该推荐",
    "这个估算",
    "该估算",
    "这个结果",
    "该结果",
    "为什么更推荐",
    "为什么推荐",
    "为什么这么推荐",
    "为什么这样推荐",
    "为什么这么建议",
    "为什么这样建议",
    "为啥推荐",
    "为啥这么推荐",
    "为啥这样推荐",
    "你刚才推荐",
    "刚才推荐",
    "刚才那个推荐",
    "刚才那个估算",
    "这个建议",
    "这个方案",
)
COMPARISON_CONNECTOR_PHRASES = (
    "还是",
    "比",
    "和",
    "跟",
    "与",
)
COMPARISON_DECISION_PHRASES = (
    "更适合",
    "更好",
    "更值得",
    "更稳妥",
    "怎么选",
    "选哪个",
    "该选",
)
SWAP_REQUEST_PHRASES = (
    "换成",
    "换掉",
    "替代",
    "替换",
    "平替",
)
SWAP_DECISION_PHRASES = (
    "什么",
    "哪个",
    "推荐",
    "更",
    "可以吗",
    "行吗",
    "好吗",
)
BRANDED_GENERIC_PRODUCT_BRANDS = (
    "麦当劳",
    "肯德基",
    "kfc",
    "汉堡王",
    "burgerking",
    "华莱士",
    "塔斯汀",
    "德克士",
    "霸王茶姬",
    "喜茶",
    "奈雪",
    "奈雪的茶",
    "沪上阿姨",
    "古茗",
    "茶百道",
    "coco",
    "一点点",
    "蜜雪冰城",
    "星巴克",
    "瑞幸",
)
BRANDED_GENERIC_PRODUCT_TERMS = (
    "汉堡",
    "牛堡",
    "鸡堡",
    "奶茶",
    "咖啡",
    "果茶",
    "饮品",
    "炸鸡",
    "薯条",
)
BRANDED_GENERIC_DETAIL_HINTS = (
    "双层",
    "单层",
    "吉士",
    "芝士",
    "板烧",
    "麦香鸡",
    "麦辣",
    "巨无霸",
    "伯牙绝弦",
    "幽兰",
    "生椰",
    "拿铁",
    "美式",
    "珍珠",
    "椰云",
    "冰",
    "热",
    "大杯",
    "中杯",
    "小杯",
    "三分糖",
    "五分糖",
    "七分糖",
    "无糖",
    "少冰",
    "去冰",
    "套餐",
)
DECISION_PROMOTION_ONLY_PHRASES = (
    "限时优惠",
    "限时特惠",
    "今日特价",
    "买一送一",
    "第二杯半价",
    "第二份半价",
    "满减",
    "立减",
    "折扣",
    "优惠",
    "特价",
    "爆款",
    "热销",
)
DECISION_PRODUCT_INPUT_HINTS = (
    *FOOD_QUANTITY_PATTERNS,
    *BRANDED_GENERIC_PRODUCT_BRANDS,
    *BRANDED_GENERIC_PRODUCT_TERMS,
    *BRANDED_GENERIC_DETAIL_HINTS,
    "套餐",
    "汉堡",
    "薯条",
    "可乐",
    "奶茶",
    "果茶",
    "咖啡",
    "拿铁",
    "美式",
)
DECISION_NON_PRODUCT_REQUEST_PHRASES = (
    *RECOMMENDATION_ROUTE_PHRASES,
    *TEXT_ROUTE_PHRASES,
    *AMBIGUOUS_PHRASES,
)


def create_empty_session(user_id: int) -> dict[str, object]:
    conn = get_db_connection()
    try:
        return create_session_record(conn, user_id, DEFAULT_SESSION_TITLE)
    finally:
        conn.close()


def create_session_with_first_user_message(
    user_id: int,
    content: str,
    *,
    created_at: str | None = None,
    mode: str = DEFAULT_CHAT_INPUT_MODE,
) -> dict[str, object]:
    conn = get_db_connection()
    try:
        session = create_session_record(conn, user_id, DEFAULT_SESSION_TITLE)
        _append_user_message_with_conn(
            conn,
            user_id,
            int(session["id"]),
            content,
            created_at=created_at,
            mode=mode,
        )
        return _get_session_detail_with_conn(conn, int(session["id"]), user_id)
    finally:
        conn.close()


def create_session_and_reply(
    user_id: int,
    content: str,
    *,
    profile_id: int | None = None,
    mode: str = DEFAULT_CHAT_INPUT_MODE,
) -> dict[str, object]:
    conn = get_db_connection()
    try:
        session_detail = create_session_with_first_user_message(
            user_id,
            content,
            mode=mode,
        )
        session_id = int(session_detail["id"])
        user_message = session_detail["messages"][0]
        assistant_message = _generate_assistant_reply_with_conn(
            conn,
            user_id,
            session_id,
            content,
            profile_id,
            mode=mode,
        )
        session = _get_session_detail_with_conn(conn, session_id, user_id)
        return {
            "session": session,
            "user_message": user_message,
            "assistant_message": assistant_message,
        }
    finally:
        conn.close()


def append_user_message(
    user_id: int,
    session_id: int,
    content: str,
    *,
    created_at: str | None = None,
    mode: str = DEFAULT_CHAT_INPUT_MODE,
) -> dict[str, object] | None:
    conn = get_db_connection()
    try:
        return _append_user_message_with_conn(
            conn,
            user_id,
            session_id,
            content,
            created_at=created_at,
            mode=mode,
        )
    finally:
        conn.close()


def send_message_in_session(
    user_id: int,
    session_id: int,
    content: str,
    *,
    profile_id: int | None = None,
    mode: str = DEFAULT_CHAT_INPUT_MODE,
) -> dict[str, object] | None:
    conn = get_db_connection()
    try:
        user_message = _append_user_message_with_conn(
            conn,
            user_id,
            session_id,
            content,
            mode=mode,
        )
        if user_message is None:
            return None

        assistant_message = _generate_assistant_reply_with_conn(
            conn,
            user_id,
            session_id,
            content,
            profile_id,
            mode=mode,
        )
        session = _get_session_detail_with_conn(conn, session_id, user_id)
        return {
            "session": session,
            "user_message": user_message,
            "assistant_message": assistant_message,
        }
    finally:
        conn.close()


def append_assistant_message(
    user_id: int,
    session_id: int,
    *,
    message_type: str = TEXT_MESSAGE_TYPE,
    content: str | None = None,
    result_title: str | None = None,
    result_confidence: str | None = None,
    result_description: str | None = None,
    result_items_json: str | None = None,
    result_total: str | None = None,
    created_at: str | None = None,
) -> dict[str, object] | None:
    conn = get_db_connection()
    try:
        session = get_session_by_id_record(conn, session_id, user_id)
        if session is None:
            return None

        message = create_message_record(
            conn,
            session_id,
            user_id,
            "assistant",
            message_type,
            content=content,
            result_title=result_title,
            result_confidence=result_confidence,
            result_description=result_description,
            result_items_json=result_items_json,
            result_total=result_total,
            created_at=created_at,
            auto_commit=message_type != "estimate_result",
        )
        if message_type == "estimate_result":
            conn.commit()
        return message
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def rename_session(
    user_id: int,
    session_id: int,
    title: str,
) -> dict[str, object] | None:
    conn = get_db_connection()
    try:
        return update_session_title_record(conn, session_id, user_id, _normalize_title(title))
    finally:
        conn.close()


def delete_session(user_id: int, session_id: int) -> bool:
    conn = get_db_connection()
    try:
        # Chat sessions are deleted permanently rather than soft-deleted.
        return delete_session_record(conn, session_id, user_id)
    finally:
        conn.close()


def get_session_detail(
    user_id: int,
    session_id: int,
) -> dict[str, object] | None:
    conn = get_db_connection()
    try:
        return _get_session_detail_with_conn(conn, session_id, user_id)
    finally:
        conn.close()


def list_user_sessions(user_id: int) -> list[dict[str, object]]:
    conn = get_db_connection()
    try:
        return list_sessions_by_user_record(conn, user_id)
    finally:
        conn.close()


def _append_user_message_with_conn(
    conn,
    user_id: int,
    session_id: int,
    content: str,
    *,
    created_at: str | None = None,
    mode: str = DEFAULT_CHAT_INPUT_MODE,
) -> dict[str, object] | None:
    session = get_session_by_id_record(conn, session_id, user_id)
    if session is None:
        return None

    existing_messages = list_messages_by_session_record(conn, session_id, user_id)
    message = create_message_record(
        conn,
        session_id,
        user_id,
        "user",
        "text",
        content=content,
        payload_json=json.dumps(
            {
                "text": content,
                "mode": mode if mode == DECISION_CHAT_INPUT_MODE else DEFAULT_CHAT_INPUT_MODE,
            },
            ensure_ascii=False,
        ),
        created_at=created_at,
    )

    if not existing_messages:
        update_session_title_record(
            conn,
            session_id,
            user_id,
            _build_title_from_first_message(content),
        )

    return message


def _get_session_detail_with_conn(
    conn,
    session_id: int,
    user_id: int,
) -> dict[str, object] | None:
    session = get_session_by_id_record(conn, session_id, user_id)
    if session is None:
        return None

    session_detail = dict(session)
    session_detail["messages"] = list_messages_by_session_record(conn, session_id, user_id)
    return session_detail


def _generate_assistant_reply_with_conn(
    conn,
    user_id: int,
    session_id: int,
    content: str,
    profile_id: int | None,
    *,
    mode: str = DEFAULT_CHAT_INPUT_MODE,
) -> dict[str, object]:
    message_type = DEFAULT_RESOLVED_MESSAGE_TYPE
    try:
        message_type = resolve_message_type(
            content,
            profile_id=profile_id,
            user_id=user_id,
            mode=mode,
        )
        assistant_message = build_response_by_type(
            conn,
            user_id,
            session_id,
            content=content,
            profile_id=profile_id,
            message_type=message_type,
            mode=mode,
        )
    except Exception as exc:
        conn.rollback()
        assistant_message = create_message_record(
            conn,
            session_id,
            user_id,
            "assistant",
            TEXT_MESSAGE_TYPE,
            content=_build_fallback_message(exc, message_type=message_type),
        )
    return assistant_message


def resolve_message_type(
    content: str,
    *,
    profile_id: int | None,
    user_id: int,
    mode: str = DEFAULT_CHAT_INPUT_MODE,
) -> str:
    del profile_id, user_id
    normalized_content = _normalize_routing_text(content)

    if mode == DECISION_CHAT_INPUT_MODE:
        return _resolve_decision_mode_message_type(normalized_content)

    is_text_request = _matches_text_request(normalized_content)
    is_recommendation_request = _matches_recommendation_request(normalized_content)
    is_estimate_request = _matches_estimate_request(normalized_content)
    needs_clarification = _contains_any_phrase(
        normalized_content,
        AMBIGUOUS_PHRASES,
    ) and not _looks_like_food_description(normalized_content)

    # Only explicit explanatory follow-ups should let `text` override
    # recommendation signals. This reduces high-frequency misroutes for
    # comparison/swap requests containing words like "区别/为什么".
    if _is_explanatory_follow_up(normalized_content, has_text_signal=is_text_request):
        return TEXT_MESSAGE_TYPE

    if _needs_branded_generic_product_clarification(normalized_content):
        return CLARIFICATION_NEEDED

    if _needs_standard_dish_estimate_clarification(normalized_content):
        return CLARIFICATION_NEEDED

    if is_estimate_request:
        if _needs_standard_dish_estimate_clarification(normalized_content):
            return CLARIFICATION_NEEDED
        return DEFAULT_RESOLVED_MESSAGE_TYPE

    if is_recommendation_request:
        return RECOMMENDATION_MESSAGE_TYPE

    if is_text_request:
        return TEXT_MESSAGE_TYPE

    # 无明确推荐/估算信号，且包含模糊表述，且不像食物描述 -> 澄清提问
    if needs_clarification:
        return CLARIFICATION_NEEDED

    return DEFAULT_RESOLVED_MESSAGE_TYPE


def build_response_by_type(
    conn,
    user_id: int,
    session_id: int,
    *,
    content: str,
    profile_id: int | None,
    message_type: str,
    mode: str = DEFAULT_CHAT_INPUT_MODE,
) -> dict[str, object]:
    if message_type == CLARIFICATION_NEEDED:
        clarification_message = _build_clarification_message(content, mode=mode)
        clarification_decision_card = build_clarification_decision_card(
            input_summary=content,
            container_type="chat_message",
            reason=_resolve_clarification_reason(content, mode=mode),
        )
        return _create_text_message_with_conn(
            conn,
            user_id,
            session_id,
            content=clarification_message,
            decision_card=clarification_decision_card.model_dump(by_alias=True),
        )
    if message_type == MEAL_ESTIMATE_MESSAGE_TYPE:
        return _build_meal_estimate_response_with_conn(
            conn,
            user_id,
            session_id,
            content=content,
            profile_id=profile_id,
        )
    if message_type == RECOMMENDATION_MESSAGE_TYPE:
        return _build_meal_recommendation_response_with_conn(
            conn,
            user_id,
            session_id,
            content=content,
            profile_id=profile_id,
        )
    if message_type == TEXT_MESSAGE_TYPE:
        return _build_text_response_with_conn(
            conn,
            user_id,
            session_id,
            content=content,
            profile_id=profile_id,
        )

    raise ValueError(f"Unsupported message_type: {message_type}")


def _build_meal_estimate_response_with_conn(
    conn,
    user_id: int,
    session_id: int,
    *,
    content: str,
    profile_id: int | None,
) -> dict[str, object]:
    estimate = estimate_meal(content, profile_id, user_id)
    estimates = split_estimate_by_items(estimate, query=content)
    return _create_estimate_result_message_with_conn(
        conn,
        user_id,
        session_id,
        query=content,
        estimate=estimate,
        estimates=estimates,
        profile_id=profile_id,
    )


def _build_meal_recommendation_response_with_conn(
    conn,
    user_id: int,
    session_id: int,
    *,
    content: str,
    profile_id: int | None,
) -> dict[str, object]:
    recommendation = generate_meal_recommendation(content, profile_id, user_id)
    profile_allergies: list[str] = []
    if profile_id is not None:
        profile = get_profile(profile_id, user_id)
        if profile is not None and getattr(profile, "allergies", None):
            profile_allergies = list(profile.allergies)

    # Post-check recommendation safety using three sources:
    # 1) profile allergens, 2) explicit user restrictions in this query,
    # 3) lightweight contraindication cues (e.g. 痛风/高血压/糖尿病).
    ok, violations = check_allergen_violations(
        {
            "title": recommendation.title,
            "description": recommendation.description,
            "response": recommendation.response,
        },
        profile_allergies,
        user_query=content,
    )
    if not ok and violations:
        violations_str = "、".join(str(v) for v in violations)
        warning_title = "推荐已拦截（触发安全限制）"
        warning_description = (
            f"系统检测到推荐内容与以下限制冲突：{violations_str}。"
            "为避免风险，本次不展示原始推荐结果。"
        )
        warning_content = (
            f"由于推荐内容可能违反你的过敏原、禁忌或显式限制（{violations_str}），本次推荐已被系统拦截。"
            "你可以：\n"
            "- 在 Profile 中确认或更新过敏原信息；\n"
            "- 在问题里继续明确“不要包含哪些食材”；\n"
            "- 或改问其他不含这些限制项的选择。"
        )
        return _create_meal_recommendation_message_with_conn(
            conn,
            user_id,
            session_id,
            title=warning_title,
            description=warning_description,
            content=warning_content,
            knowledge_refs=None,
        )

    return _create_meal_recommendation_message_with_conn(
        conn,
        user_id,
        session_id,
        title=recommendation.title,
        description=recommendation.description,
        content=recommendation.response,
        knowledge_refs=getattr(recommendation, "knowledge_refs", None),
    )


def _build_text_response_with_conn(
    conn,
    user_id: int,
    session_id: int,
    *,
    content: str,
    profile_id: int | None,
) -> dict[str, object]:
    reply = generate_text_reply(content, profile_id, user_id)
    return _create_text_message_with_conn(
        conn,
        user_id,
        session_id,
        content=reply.response,
        knowledge_refs=getattr(reply, "knowledge_refs", None),
    )


def _create_estimate_result_message_with_conn(
    conn,
    user_id: int,
    session_id: int,
    *,
    query: str,
    estimate,
    estimates: list | None = None,
    profile_id: int | None = None,
) -> dict[str, object]:
    # Chat analysis results stay in the conversation only. Food Log is an explicit
    # save action and must not be created automatically from successful analysis.
    # When multiple foods: store estimates array in payload for per-item display;
    # keep result_* as combined for Food Log save compatibility.
    estimates_list = estimates if estimates is not None else [estimate]
    knowledge_refs = getattr(estimate, "knowledge_refs", None)
    profile = None
    if profile_id is not None:
        profile = get_profile(profile_id, user_id)
    decision_card = build_decision_card_from_estimate(
        input_summary=query,
        title=estimate.title,
        confidence=estimate.confidence,
        description=estimate.description,
        items=estimate.items,
        total_calories=estimate.total_calories,
        suggestion=estimate.suggestion,
        container_type="chat_message",
        profile=profile,
        profile_requested=profile_id is not None,
    )
    payload_obj: dict[str, object] = {
        "decision_card": decision_card.model_dump(by_alias=True),
        "suggestion": estimate.suggestion,
    }
    if len(estimates_list) > 1:
        payload_obj["estimates"] = [
            {
                "title": e.title,
                "confidence": e.confidence,
                "description": e.description,
                "items": [item.model_dump() for item in e.items],
                "total": e.total_calories,
            }
            for e in estimates_list
        ]
    if knowledge_refs:
        payload_obj["knowledge_refs"] = [
            ref.model_dump() if hasattr(ref, "model_dump") else ref
            for ref in knowledge_refs
        ]
    payload_json = json.dumps(payload_obj, ensure_ascii=False)

    assistant_message = create_message_record(
        conn,
        session_id,
        user_id,
        "assistant",
        "estimate_result",
        content=estimate.suggestion,
        result_title=estimate.title,
        result_confidence=estimate.confidence,
        result_description=estimate.description,
        result_items_json=json.dumps(
            [item.model_dump() for item in estimate.items],
            ensure_ascii=False,
        ),
        result_total=estimate.total_calories,
        payload_json=payload_json,
        auto_commit=False,
    )
    conn.commit()
    return assistant_message


def _create_meal_recommendation_message_with_conn(
    conn,
    user_id: int,
    session_id: int,
    *,
    title: str,
    description: str,
    content: str,
    knowledge_refs: list | None,
) -> dict[str, object]:
    payload_obj: dict[str, object] = {
        "title": title,
        "description": description,
    }
    if knowledge_refs:
        payload_obj["knowledge_refs"] = [
            ref.model_dump() if hasattr(ref, "model_dump") else ref
            for ref in knowledge_refs
        ]
    payload_json = json.dumps(payload_obj, ensure_ascii=False)
    return create_message_record(
        conn,
        session_id,
        user_id,
        "assistant",
        RECOMMENDATION_MESSAGE_TYPE,
        content=content,
        payload_json=payload_json,
    )


def _create_text_message_with_conn(
    conn,
    user_id: int,
    session_id: int,
    *,
    content: str,
    knowledge_refs: list | None = None,
    decision_card: dict[str, object] | None = None,
) -> dict[str, object]:
    payload_obj: dict[str, object] = {"text": content}
    if decision_card:
        payload_obj["decision_card"] = decision_card
    if knowledge_refs:
        payload_obj["knowledge_refs"] = [
            ref.model_dump() if hasattr(ref, "model_dump") else ref
            for ref in knowledge_refs
        ]
    return create_message_record(
        conn,
        session_id,
        user_id,
        "assistant",
        TEXT_MESSAGE_TYPE,
        content=content,
        payload_json=json.dumps(payload_obj, ensure_ascii=False),
    )


def _build_fallback_message(
    error: Exception,
    *,
    message_type: str = DEFAULT_RESOLVED_MESSAGE_TYPE,
) -> str:
    user_message = getattr(error, "user_message", None)
    if isinstance(user_message, str) and user_message.strip():
        return user_message
    if message_type == RECOMMENDATION_MESSAGE_TYPE:
        return DEFAULT_RECOMMENDATION_ERROR_MESSAGE
    if message_type == TEXT_MESSAGE_TYPE:
        return DEFAULT_TEXT_ERROR_MESSAGE
    return DEFAULT_ESTIMATE_ERROR_MESSAGE


def _build_title_from_first_message(content: str) -> str:
    normalized = _normalize_title(content)
    if len(normalized) <= MAX_SESSION_TITLE_LENGTH:
        return normalized
    return f"{normalized[: MAX_SESSION_TITLE_LENGTH - 3]}..."


def _normalize_title(value: str) -> str:
    return " ".join(value.strip().split())


def _normalize_routing_text(value: str) -> str:
    return " ".join(value.lower().strip().split())


def _matches_text_request(value: str) -> bool:
    return _contains_any_phrase(value, TEXT_ROUTE_PHRASES)


def _matches_recommendation_request(value: str) -> bool:
    if _matches_estimate_request(value):
        return False
    if _contains_any_phrase(
        value,
        RECOMMENDATION_ROUTE_PHRASES + ADDITIONAL_RECOMMENDATION_ROUTE_PHRASES,
    ):
        return True
    return _looks_like_comparison_or_swap_recommendation(value)


def _matches_estimate_request(value: str) -> bool:
    return _contains_any_phrase(value, ESTIMATE_ROUTE_PHRASES) or _has_nutrition_quantity_question(value)


def _is_explanatory_follow_up(value: str, *, has_text_signal: bool) -> bool:
    if not has_text_signal:
        return False
    return _contains_any_phrase(value, EXPLANATORY_FOLLOW_UP_PHRASES)


def _contains_any_phrase(value: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in value for phrase in phrases)


def _looks_like_comparison_or_swap_recommendation(value: str) -> bool:
    has_comparison_connector = _contains_any_phrase(value, COMPARISON_CONNECTOR_PHRASES)
    if has_comparison_connector and _contains_any_phrase(value, COMPARISON_DECISION_PHRASES):
        return True

    has_swap_signal = _contains_any_phrase(value, SWAP_REQUEST_PHRASES)
    if has_swap_signal and _contains_any_phrase(value, SWAP_DECISION_PHRASES):
        return True

    return False


def _has_nutrition_quantity_question(value: str) -> bool:
    if not _contains_any_phrase(value, NUTRITION_TOPIC_PHRASES):
        return False
    return _contains_any_phrase(value, NUTRITION_QUANTITY_PHRASES)


def _looks_like_food_description(value: str) -> bool:
    """输入是否像食物描述（含量词或典型食物词），用于避免将「一碗面吃什么」误判为需澄清。"""
    return _contains_any_phrase(value, FOOD_QUANTITY_PATTERNS)


def _is_specific_ambiguous_standard_dish_query(value: str) -> bool:
    """
    对「套餐/盖饭/炒面」这类词做轻量判定：
    - 若出现了非泛化修饰（如「板烧鸡腿堡套餐」），按可估算处理；
    - 若仅是「套餐热量多少」等泛化问法，仍走澄清。
    """
    normalized_value = value
    for prefix in GENERIC_AMBIGUOUS_DISH_PREFIXES:
        if normalized_value.startswith(prefix):
            normalized_value = normalized_value[len(prefix):]
            break

    if any(
        generic in value
        for generic in (
            "套餐",
            "炒面",
            "盖饭",
            "炒饭",
            "拌饭",
            "盖浇饭",
            "米线",
        )
    ):
        patterns = (
            r"[\u4e00-\u9fff]{2,}套餐",
            r"[\u4e00-\u9fff]{2,}炒面",
            r"[\u4e00-\u9fff]{2,}盖饭",
            r"[\u4e00-\u9fff]{2,}炒饭",
            r"[\u4e00-\u9fff]{2,}拌饭",
            r"[\u4e00-\u9fff]{2,}盖浇饭",
            r"[\u4e00-\u9fff]{2,}米线",
        )
        for pattern in patterns:
            matched = re.search(pattern, normalized_value)
            if not matched:
                continue
            phrase = matched.group(0)
            if any(phrase.startswith(prefix) for prefix in GENERIC_AMBIGUOUS_DISH_PREFIXES):
                continue
            return True
    return False


def _needs_standard_dish_estimate_clarification(value: str) -> bool:
    if not query_needs_standard_dish_clarification(value):
        return False
    if _is_specific_ambiguous_standard_dish_query(value):
        return False
    return _contains_any_phrase(value, AMBIGUOUS_STANDARD_DISH_ESTIMATE_HINTS)


def _resolve_decision_mode_message_type(value: str) -> str:
    if _looks_like_missing_product_subject_request(value):
        return CLARIFICATION_NEEDED

    if _is_brand_only_input(value):
        return CLARIFICATION_NEEDED

    if _needs_branded_generic_product_clarification(value):
        return CLARIFICATION_NEEDED

    if _needs_standard_dish_estimate_clarification(value):
        return CLARIFICATION_NEEDED

    return DEFAULT_RESOLVED_MESSAGE_TYPE


def _looks_like_missing_product_subject_request(value: str) -> bool:
    if _looks_like_promotion_only_decision_input(value):
        return True

    return (
        _contains_any_phrase(value, DECISION_NON_PRODUCT_REQUEST_PHRASES)
        and not _contains_any_phrase(value, DECISION_PRODUCT_INPUT_HINTS)
    )


def _looks_like_promotion_only_decision_input(value: str) -> bool:
    if not _contains_any_phrase(value, DECISION_PROMOTION_ONLY_PHRASES):
        return False

    return not _contains_any_phrase(value, DECISION_PRODUCT_INPUT_HINTS)


def _is_brand_only_input(value: str) -> bool:
    compact_value = value.replace(" ", "")
    return compact_value in BRANDED_GENERIC_PRODUCT_BRANDS


def _resolve_clarification_reason(content: str, *, mode: str) -> str:
    normalized_content = _normalize_routing_text(content)
    if mode == DECISION_CHAT_INPUT_MODE:
        if _looks_like_missing_product_subject_request(normalized_content):
            return "missing_product_subject"
        if (
            _is_brand_only_input(normalized_content)
            or _needs_branded_generic_product_clarification(normalized_content)
            or _needs_standard_dish_estimate_clarification(normalized_content)
        ):
            return "missing_product_detail"
    return "missing_key_fields"


def _build_clarification_message(content: str, *, mode: str = DEFAULT_CHAT_INPUT_MODE) -> str:
    normalized_content = _normalize_routing_text(content)

    if mode == DECISION_CHAT_INPUT_MODE and _looks_like_missing_product_subject_request(normalized_content):
        return DECISION_PRODUCT_SUBJECT_CLARIFICATION_MESSAGE

    if mode == DECISION_CHAT_INPUT_MODE and (
        _is_brand_only_input(normalized_content)
        or _needs_branded_generic_product_clarification(normalized_content)
        or _needs_standard_dish_estimate_clarification(normalized_content)
    ):
        return PRODUCT_DETAIL_CLARIFICATION_MESSAGE

    if _needs_branded_generic_product_clarification(normalized_content):
        return PRODUCT_DETAIL_CLARIFICATION_MESSAGE

    return CLARIFICATION_MESSAGE


def _needs_branded_generic_product_clarification(value: str) -> bool:
    compact_value = value.replace(" ", "")
    if not compact_value:
        return False
    if any(connector in compact_value for connector in COMPARISON_CONNECTOR_PHRASES):
        return False

    matched_brand = next(
        (brand for brand in BRANDED_GENERIC_PRODUCT_BRANDS if brand in compact_value),
        None,
    )
    if matched_brand is None:
        return False

    matched_generic_term = next(
        (
            generic_term
            for generic_term in BRANDED_GENERIC_PRODUCT_TERMS
            if generic_term in compact_value
        ),
        None,
    )
    if matched_generic_term is None:
        return False

    if any(detail_hint in compact_value for detail_hint in BRANDED_GENERIC_DETAIL_HINTS):
        return False

    remainder = compact_value.replace(matched_brand, "", 1)
    remainder = remainder.replace(matched_generic_term, "", 1)
    remainder = re.sub(r"(热量|卡路里|多少|大概|营养|蛋白质|碳水|脂肪|能量|吗)", "", remainder)
    return len(remainder) < 2


def estimate_meal(query: str, profile_id: int | None, user_id: int):
    from backend.services.estimate import estimate_meal as estimate_meal_impl

    return estimate_meal_impl(query, profile_id, user_id)
