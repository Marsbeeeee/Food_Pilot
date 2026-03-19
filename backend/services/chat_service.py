import json

from backend.database.connection import get_db_connection
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
from backend.services.recommendation import (
    generate_meal_recommendation,
    generate_text_reply,
    check_allergen_violations,
)
from backend.services.profile_service import get_profile


DEFAULT_SESSION_TITLE = "New chat"
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
TEXT_ROUTE_PHRASES = (
    "你好",
    "谢谢",
    "为什么",
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
# 食物描述常见量词，用于区分「模糊提问」与「食物描述」
FOOD_QUANTITY_PATTERNS = (
    "一碗", "两碗", "一份", "两份", "一杯", "两杯",
    "一个", "两个", "半个", "一根", "两根",
)
ADDITIONAL_RECOMMENDATION_ROUTE_PHRASES = (
    "更值得选",
    "换掉",
    "更好的替代",
    "替代",
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
        )
        return _get_session_detail_with_conn(conn, int(session["id"]), user_id)
    finally:
        conn.close()


def create_session_and_reply(
    user_id: int,
    content: str,
    *,
    profile_id: int | None = None,
) -> dict[str, object]:
    conn = get_db_connection()
    try:
        session_detail = create_session_with_first_user_message(
            user_id,
            content,
        )
        session_id = int(session_detail["id"])
        user_message = session_detail["messages"][0]
        assistant_message = _generate_assistant_reply_with_conn(
            conn,
            user_id,
            session_id,
            content,
            profile_id,
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
) -> dict[str, object] | None:
    conn = get_db_connection()
    try:
        return _append_user_message_with_conn(
            conn,
            user_id,
            session_id,
            content,
            created_at=created_at,
        )
    finally:
        conn.close()


def send_message_in_session(
    user_id: int,
    session_id: int,
    content: str,
    *,
    profile_id: int | None = None,
) -> dict[str, object] | None:
    conn = get_db_connection()
    try:
        user_message = _append_user_message_with_conn(
            conn,
            user_id,
            session_id,
            content,
        )
        if user_message is None:
            return None

        assistant_message = _generate_assistant_reply_with_conn(
            conn,
            user_id,
            session_id,
            content,
            profile_id,
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
) -> dict[str, object]:
    message_type = DEFAULT_RESOLVED_MESSAGE_TYPE
    try:
        message_type = resolve_message_type(
            content,
            profile_id=profile_id,
            user_id=user_id,
        )
        assistant_message = build_response_by_type(
            conn,
            user_id,
            session_id,
            content=content,
            profile_id=profile_id,
            message_type=message_type,
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
) -> str:
    del profile_id, user_id
    normalized_content = _normalize_routing_text(content)

    if _matches_text_request(normalized_content):
        return TEXT_MESSAGE_TYPE

    if _matches_recommendation_request(normalized_content):
        return RECOMMENDATION_MESSAGE_TYPE

    if _matches_estimate_request(normalized_content):
        return DEFAULT_RESOLVED_MESSAGE_TYPE

    # 无明确推荐/估算信号，且包含模糊表述，且不像食物描述 -> 澄清提问
    if _contains_any_phrase(normalized_content, AMBIGUOUS_PHRASES) and not _looks_like_food_description(
        normalized_content
    ):
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
) -> dict[str, object]:
    if message_type == CLARIFICATION_NEEDED:
        return _create_text_message_with_conn(
            conn,
            user_id,
            session_id,
            content=CLARIFICATION_MESSAGE,
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
    estimates = split_estimate_by_items(estimate)
    return _create_estimate_result_message_with_conn(
        conn,
        user_id,
        session_id,
        estimate=estimate,
        estimates=estimates,
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

    # If we have a profile with recorded allergies, run a simple safety check
    # to avoid returning recommendations that contain those allergens.
    if profile_id is not None:
        profile = get_profile(profile_id, user_id)
        if profile is not None and getattr(profile, "allergies", None):
            ok, violations = check_allergen_violations(
                {
                    "title": recommendation.title,
                    "description": recommendation.description,
                    "response": recommendation.response,
                },
                list(profile.allergies),
            )
            if not ok and violations:
                violations_str = "、".join(str(v) for v in violations)
                warning_title = "推荐已拦截（与过敏原冲突）"
                warning_description = (
                    f"你的档案中标记了以下过敏原：{violations_str}。"
                    "为避免风险，本次不展示包含这些成分的推荐结果。"
                )
                warning_content = (
                    f"由于推荐内容可能包含你过敏的食物（{violations_str}），本次推荐已被系统拦截。"
                    "你可以：\n"
                    "- 在 Profile 中确认或更新过敏原信息；\n"
                    "- 在提问时明确强调“不要包含这些成分”；\n"
                    "- 或改问其他不含这些过敏原的选择。"
                )
                return _create_meal_recommendation_message_with_conn(
                    conn,
                    user_id,
                    session_id,
                    title=warning_title,
                    description=warning_description,
                    content=warning_content,
                )

    return _create_meal_recommendation_message_with_conn(
        conn,
        user_id,
        session_id,
        title=recommendation.title,
        description=recommendation.description,
        content=recommendation.response,
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
    )


def _create_estimate_result_message_with_conn(
    conn,
    user_id: int,
    session_id: int,
    *,
    estimate,
    estimates: list | None = None,
) -> dict[str, object]:
    # Chat analysis results stay in the conversation only. Food Log is an explicit
    # save action and must not be created automatically from successful analysis.
    # When multiple foods: store estimates array in payload for per-item display;
    # keep result_* as combined for Food Log save compatibility.
    estimates_list = estimates if estimates is not None else [estimate]
    payload_json: str | None = None
    if len(estimates_list) > 1:
        payload_obj = {
            "estimates": [
                {
                    "title": e.title,
                    "confidence": e.confidence,
                    "description": e.description,
                    "items": [item.model_dump() for item in e.items],
                    "total": e.total_calories,
                }
                for e in estimates_list
            ],
            "suggestion": estimate.suggestion,
        }
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
) -> dict[str, object]:
    payload_json = json.dumps(
        {
            "title": title,
            "description": description,
        },
        ensure_ascii=False,
    )
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
) -> dict[str, object]:
    return create_message_record(
        conn,
        session_id,
        user_id,
        "assistant",
        TEXT_MESSAGE_TYPE,
        content=content,
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
    return _contains_any_phrase(
        value,
        RECOMMENDATION_ROUTE_PHRASES + ADDITIONAL_RECOMMENDATION_ROUTE_PHRASES,
    )


def _matches_estimate_request(value: str) -> bool:
    return _contains_any_phrase(value, ESTIMATE_ROUTE_PHRASES)


def _contains_any_phrase(value: str, phrases: tuple[str, ...]) -> bool:
    return any(phrase in value for phrase in phrases)


def _looks_like_food_description(value: str) -> bool:
    """输入是否像食物描述（含量词或典型食物词），用于避免将「一碗面吃什么」误判为需澄清。"""
    return _contains_any_phrase(value, FOOD_QUANTITY_PATTERNS)


def estimate_meal(query: str, profile_id: int | None, user_id: int):
    from backend.services.estimate import estimate_meal as estimate_meal_impl

    return estimate_meal_impl(query, profile_id, user_id)
