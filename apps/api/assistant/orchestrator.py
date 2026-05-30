from __future__ import annotations

from copy import deepcopy
from datetime import timedelta
import json
import logging
import re
from typing import Any

from django.utils import timezone

from .agent import AgentCallError, call_agent, call_agent_json
from .services import build_assistant_reply_with_history
from .skills import SKILLS, _guess_kind


logger = logging.getLogger(__name__)
ASSISTANT_DEBUG = True


def _assistant_debug(message: str, *args: Any) -> None:
    if not ASSISTANT_DEBUG:
        return
    logger.warning(message, *args)
    try:
        print(message % args, flush=True)
    except Exception:
        print(message, *args, flush=True)


YES_WORDS = (
    "好",
    "好的",
    "好呀",
    "好啊",
    "可以",
    "行",
    "行的",
    "没问题",
    "合适",
    "就这样",
    "就这样吧",
    "不用改了",
    "按这个",
    "挺好",
    "可以了",
    "很好",
    "确认",
    "确定",
    "生成",
    "安排",
    "走",
    "ok",
    "OK",
    "嗯",
    "嗯嗯",
    "对",
    "对的",
    "是的",
)
NEGATIVE_CONFIRMATION_WORDS = ("不", "别", "不要", "不行", "不可以", "先别", "算了", "等等", "等下", "不是")
NO_REVISION_CONFIRM_WORDS = (
    "不用调整",
    "不用改",
    "不用修改",
    "不用再改",
    "不用再调整",
    "不需要调整",
    "不需要改",
    "不需要修改",
    "无需调整",
    "无需修改",
    "无需再改",
    "没问题不用改",
    "不用动",
    "不用变",
)
GENERATE_WORDS = (
    "生成动作建议",
    "直接生成",
    "帮我生成",
    "弹出动作",
    "生成吧",
    "去生成",
    "直接给我动作",
    "生成卡片",
    "执行成卡片",
    "弹卡片",
    "弹出卡片",
    "变成卡片",
    "出卡片",
    "做成卡片",
    "转成卡片",
)
SELF_FILL_WORDS = ("我自己填写", "我自己填", "我自己来", "只填充", "直接填充", "我先自己改")
REVISE_WORDS = ("修改", "改成", "改一下", "优化", "润色", "重写", "太短", "太长", "更")

FORUM_CATEGORIES = ("校园日常", "学习交流", "活动组局", "实习求职", "项目合作", "组队招募", "情绪树洞")
TRADE_TYPE_MAP = {
    "出售": "sell",
    "卖": "sell",
    "闲置": "sell",
    "求购": "buy",
    "收": "buy",
    "交换": "exchange",
    "互换": "exchange",
    "服务": "service",
    "代做": "service",
}
TRADE_TYPE_LABELS = {
    "sell": "出售",
    "buy": "求购",
    "exchange": "交换",
    "service": "服务",
}
COMMON_SKILLS = (
    "前端",
    "后端",
    "设计",
    "产品",
    "算法",
    "运营",
    "文案",
    "拍摄",
    "剪辑",
    "建模",
    "测试",
    "数据分析",
    "小程序",
    "Python",
    "Java",
)
DATING_PREFERENCE_KEYWORDS = ("真诚", "开朗", "温柔", "靠谱", "幽默", "稳定", "上进", "阳光", "好沟通", "边界感", "同频", "认真")
STUDY_CATEGORY_KEYWORDS = ("学习", "复习", "高数", "考试", "自习", "图书馆", "课程", "作业", "考研", "四六级")
TEAM_INTENT_KEYWORDS = ("小程序", "项目", "前端", "后端", "队友", "组队", "招募", "目标", "开发", "产品", "设计", "算法")
TRADE_OBJECT_KEYWORDS = ("出", "出售", "卖", "转让", "闲置", "求购", "收", "交换", "换", "价格", "元", "可小刀", "面交", "成新")
TRADE_SELL_KEYWORDS = ("出", "出售", "卖", "转让", "闲置")
TRADE_BUY_KEYWORDS = ("求购", "收", "想买")
TRADE_EXCHANGE_KEYWORDS = ("交换", "互换", "换")
TRADE_SERVICE_KEYWORDS = ("服务", "代做", "帮忙")
AGENT_ALLOWED_INTENTS = {
    "forum_post_create",
    "dating_setup",
    "team_post_create",
    "trade_post_create",
    "team_apply",
    "trade_favorite",
    "context_chat_message_send",
    "chat_message_send",
    "profile_update",
    "forum_comment_create",
}
AGENT_ALLOWED_SIGNALS = {
    "new_request",
    "provide_info",
    "confirm_draft",
    "request_revision",
    "request_generate",
    "self_fill",
    "cancel",
    "unclear",
}
AGENT_ALLOWED_FLOWS = {"collecting", "confirming", "ready"}
AGENT_ALLOWED_ACTION_INTENTS = AGENT_ALLOWED_INTENTS | {"dating_profile_update", "dating_preference_update"}
AGENT_PAYLOAD_FIELDS = {
    "forum_post_create": {"title", "body", "category", "tags"},
    "forum_comment_create": {"post_id", "parent", "body"},
    "team_post_create": {"title", "summary", "details", "target_size", "tags", "required_skills"},
    "team_apply": {"post_id", "message"},
    "trade_post_create": {"post_type", "title", "description", "price", "condition", "tags", "is_negotiable"},
    "trade_favorite": {"post_id"},
    "context_chat_message_send": {"target_user_id", "source_type", "source_id", "body"},
    "profile_update": {"nickname", "headline", "bio", "gender", "major", "grade", "interests"},
    "chat_message_send": {"thread_id", "body"},
    "dating_setup": {"profile", "preference"},
}
AGENT_DATING_PROFILE_FIELDS = {"nickname", "gender", "height_cm", "weight_kg", "age", "interests", "bio", "is_visible"}
AGENT_DATING_PREFERENCE_FIELDS = {
    "preferred_genders",
    "preferred_interests",
    "min_height_cm",
    "max_height_cm",
    "min_weight_kg",
    "max_weight_kg",
    "min_age",
    "max_age",
}
PAYLOAD_GENERATION_INTENTS = {
    "forum_post_create",
    "team_post_create",
    "trade_post_create",
    "dating_setup",
    "profile_update",
}


def _empty_state() -> dict[str, Any]:
    return {
        "flow": "idle",
        "intent": "",
        "draft_kind": "",
        "draft_target_page": "",
        "collected_payload": {},
        "missing_fields": [],
        "missing_field_labels": [],
        "expanded_preview": "",
        "last_question": "",
        "question_field": "",
    }


def _normalize_state(raw: dict[str, Any] | None) -> dict[str, Any]:
    state = _empty_state()
    if not isinstance(raw, dict):
        return state
    state.update({key: raw.get(key, value) for key, value in state.items()})
    if not isinstance(state.get("collected_payload"), dict):
        state["collected_payload"] = {}
    if not isinstance(state.get("missing_fields"), list):
        state["missing_fields"] = []
    if not isinstance(state.get("missing_field_labels"), list):
        state["missing_field_labels"] = []
    return state


def _text(value: Any) -> str:
    return str(value or "").strip()


def _clean_prompt(prompt: str) -> str:
    return re.sub(r"\s+", " ", _text(prompt))


def _contains_any(prompt: str, words: tuple[str, ...]) -> bool:
    clean = _clean_prompt(prompt)
    return any(word in clean for word in words)


CASUAL_CONFIRM_WORDS = (
    "\u6ca1\u6bdb\u75c5",
    "\u6ca1\u95ee\u9898",
    "\u53ef\u4ee5\u7684",
    "\u5c31\u8fd9\u6837",
    "\u5c31\u8fd9\u6837\u5427",
    "\u4e0d\u7528\u6539",
    "\u4e0d\u7528\u8c03\u6574",
)


def _looks_like_dating_request(prompt: str) -> bool:
    clean = _clean_prompt(prompt)
    direct_words = (
        "\u604b\u7231",
        "\u4ea4\u53cb",
        "\u627e\u5bf9\u8c61",
        "\u8131\u5355",
        "\u5339\u914d",
        "\u7537\u670b\u53cb",
        "\u5973\u670b\u53cb",
    )
    profile_words = (
        "\u6211\u662f\u5973\u751f",
        "\u6211\u662f\u7537\u751f",
        "\u6027\u683c",
        "\u6162\u70ed",
        "\u771f\u8bda",
        "\u559c\u6b22",
        "\u7231\u597d",
    )
    preference_words = (
        "\u5e0c\u671b\u8ba4\u8bc6",
        "\u60f3\u8ba4\u8bc6",
        "\u60f3\u627e",
        "\u6e29\u67d4",
        "\u7a33\u5b9a",
        "\u804a\u5f97\u6765",
        "\u540c\u9891",
        "\u9760\u8c31",
    )
    return any(word in clean for word in direct_words) or (
        any(word in clean for word in profile_words) and any(word in clean for word in preference_words)
    )


def _extract_dating_preference_from_prompt(prompt: str) -> list[str]:
    clean = _clean_prompt(prompt)
    values: list[str] = []
    match = re.search(
        r"(?:\u5e0c\u671b\u8ba4\u8bc6|\u60f3\u8ba4\u8bc6|\u60f3\u627e|\u5e0c\u671b\u627e|\u671f\u5f85\u8ba4\u8bc6)([^。\uff01\uff1f\n]+)",
        clean,
    )
    if match:
        tail = re.sub(r"(\u7684\u4eba|\u7684\u5bf9\u8c61|\u7684\u670b\u53cb)$", "", match.group(1).strip())
        values.extend(item.strip() for item in re.split(r"[\u3001\uff0c,\s\u548c]+", tail) if item.strip())
    keyword_values = (
        "\u771f\u8bda",
        "\u6e29\u67d4",
        "\u7a33\u5b9a",
        "\u804a\u5f97\u6765",
        "\u9760\u8c31",
        "\u5e7d\u9ed8",
        "\u4e0a\u8fdb",
        "\u540c\u9891",
        "\u597d\u6c9f\u901a",
        "\u8fb9\u754c\u611f",
        "\u8ba4\u771f",
    )
    values.extend(keyword for keyword in keyword_values if keyword in clean)
    return list(dict.fromkeys(value for value in values if value))[:8]


def _repair_dating_payload_from_prompt(payload: dict[str, Any], prompt: str) -> dict[str, Any]:
    next_payload = deepcopy(payload)
    profile = next_payload.setdefault("profile", {})
    preference = next_payload.setdefault("preference", {})
    clean = _clean_prompt(prompt)
    if clean and len(clean) > len(_text(profile.get("bio"))):
        profile["bio"] = clean
    gender = _extract_gender(clean)
    if gender:
        profile["gender"] = gender
    if not profile.get("interests"):
        interests = _extract_interest_phrase(clean, ("\u559c\u6b22", "\u5174\u8da3", "\u7231\u597d"))
        if interests:
            profile["interests"] = interests[:6]
    preferred = _extract_dating_preference_from_prompt(clean)
    if preferred:
        current = _clean_string_list(preference.get("preferred_interests"), 8)
        preference["preferred_interests"] = list(dict.fromkeys(current + preferred))[:8]
    if "preferred_genders" not in preference:
        preference["preferred_genders"] = []
    return next_payload


def _is_short_confirmation(prompt: str) -> bool:
    clean = _clean_prompt(prompt)
    if len(clean) > 16:
        return False
    if any(word in clean for word in CASUAL_CONFIRM_WORDS):
        return True
    if any(word in clean for word in NO_REVISION_CONFIRM_WORDS):
        return True
    if any(word in clean for word in NEGATIVE_CONFIRMATION_WORDS):
        return False
    return _contains_any(clean, YES_WORDS)


def _wants_generate(prompt: str) -> bool:
    return _contains_any(prompt, GENERATE_WORDS)


def _wants_self_fill(prompt: str) -> bool:
    return _contains_any(prompt, SELF_FILL_WORDS)


def _wants_revision(prompt: str) -> bool:
    return _contains_any(prompt, REVISE_WORDS)


def _derive_title(text: str, fallback: str) -> str:
    clean = _clean_prompt(text)
    if not clean:
        return fallback
    for separator in ("。", "！", "？", "\n", ",", "，"):
        if separator in clean:
            clean = clean.split(separator, 1)[0]
            break
    clean = clean[:24].strip("：:，,。 ")
    return clean or fallback


def _fallback_title(text: str, fallback: str) -> str:
    clean = _derive_title(text, fallback)
    clean = re.sub(r"^(我想|想要|帮我|麻烦|请帮我|发一个|发一篇|写一个|写一篇|论坛帖子)", "", clean).strip("：:，,。 ")
    if len(clean) < 4:
        return fallback
    return clean[:24]


def _generate_short_title(intent_label: str, seed_text: str, fallback: str) -> str:
    clean = _clean_prompt(seed_text)
    if not clean:
        return fallback
    messages = [
        {
            "role": "system",
            "content": (
                "你是 CampusClaw 小程序里的中文标题助手。"
                "请根据正文生成一个自然、具体、不油腻的短标题。"
                "只返回标题本身，不要解释，不要加引号。"
            ),
        },
        {
            "role": "user",
            "content": f"场景：{intent_label}\n正文：{clean}\n要求：8 到 18 个中文字符，适合校园社区发布。",
        },
    ]
    try:
        title = _clean_prompt(call_agent(messages)).strip("“”\"'：:，,。 ")
    except AgentCallError:
        title = ""
    if 4 <= len(title) <= 24:
        return title
    return _fallback_title(clean, fallback)


def _looks_like_instruction(text: str) -> bool:
    clean = _clean_prompt(text)
    return any(word in clean for word in ("帮我", "我想", "想要", "生成", "写一个", "恋爱交友", "找对象", "脱单", "匹配"))


def _generate_dating_bio(seed_text: str, fallback: str) -> str:
    clean = _clean_prompt(seed_text)
    if not clean:
        return fallback
    messages = [
        {
            "role": "system",
            "content": (
                "你是 CampusClaw 小程序里的恋爱资料润色助手。"
                "把用户的表达改成第一人称自我介绍，语气自然真诚。"
                "不要编造年龄、身高、专业等用户没说的信息，只返回文本本身。"
            ),
        },
        {
            "role": "user",
            "content": f"原始表达：{clean}\n要求：35 到 80 个中文字符，适合放在恋爱匹配资料的自我介绍里。",
        },
    ]
    try:
        bio = _clean_prompt(call_agent(messages)).strip("“”\"' ")
    except AgentCallError:
        bio = ""
    if len(bio) >= 18:
        return bio
    if _looks_like_instruction(clean):
        return fallback
    return _fallback_expand_text("bio", clean, 18, fallback)


def _split_list(value: str) -> list[str]:
    raw = re.split(r"[，,、/\s]+", _text(value))
    return [item for item in (entry.strip() for entry in raw) if item]


def _extract_tag_list(prompt: str, label: str) -> list[str]:
    match = re.search(rf"{label}[：:]\s*([^\n]+)", prompt)
    if not match:
        return []
    return _split_list(match.group(1))


def _extract_label_value(prompt: str, labels: tuple[str, ...]) -> str:
    for label in labels:
        match = re.search(rf"{label}[：:]\s*([^\n]+)", prompt)
        if match:
            return _text(match.group(1))
    return ""


def _extract_first_number(prompt: str) -> float | None:
    match = re.search(r"(\d+(?:\.\d+)?)", prompt)
    return float(match.group(1)) if match else None


def _extract_int_value(prompt: str, labels: tuple[str, ...]) -> int | None:
    value = _extract_label_value(prompt, labels)
    if not value:
        return None
    match = re.search(r"\d{1,3}", value)
    return int(match.group(0)) if match else None


def _extract_int_range(prompt: str, suffix: str) -> tuple[int | None, int | None]:
    match = re.search(rf"(\d{{1,3}})\s*(?:-|到|至|~|～)\s*(\d{{1,3}})\s*{suffix}", prompt)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def _extract_gender(prompt: str) -> str:
    clean = _clean_prompt(prompt)
    if "我是男" in clean or "男生" in clean and "喜欢男生" not in clean:
        return "male"
    if "我是女" in clean or "女生" in clean and "喜欢女生" not in clean:
        return "female"
    if "其他性别" in clean:
        return "other"
    return ""


def _extract_preferred_genders(prompt: str) -> list[str]:
    clean = _clean_prompt(prompt)
    if any(word in clean for word in ("不限", "都可以", "男女都可", "都行")):
        return []
    genders: list[str] = []
    if any(word in clean for word in ("喜欢男生", "想认识男生", "希望对方是男生", "找男生")):
        genders.append("male")
    if any(word in clean for word in ("喜欢女生", "想认识女生", "希望对方是女生", "找女生")):
        genders.append("female")
    return list(dict.fromkeys(genders))


def _extract_interest_phrase(prompt: str, keywords: tuple[str, ...]) -> list[str]:
    clean = _clean_prompt(prompt)
    for keyword in keywords:
        match = re.search(rf"{keyword}([^。！？,\n]+)", clean)
        if not match:
            continue
        tail = match.group(1).strip("：:，, ")
        tail = re.sub(r"^(是|有|为|的)", "", tail).strip()
        items = re.split(r"[、,，和及/]+", tail)
        values = [item.strip() for item in items if item.strip()]
        if values:
            return values[:6]
    return []


def _extract_team_target_size(prompt: str) -> int | None:
    explicit = _extract_int_value(prompt, ("目标人数", "人数", "成员数"))
    if explicit is not None:
        return explicit
    match = re.search(r"(?:目标|规模|团队|队伍)\s*(\d{1,2})\s*(?:人|位|个)?", prompt)
    if match:
        return int(match.group(1))
    match = re.search(r"(?:找|招|需要|还差|希望有)\s*(\d{1,2})\s*(?:人|位|个)", prompt)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d{1,2})\s*(?:人|位|个).{0,8}(?:队友|同学|伙伴|成员)", prompt)
    if match:
        return int(match.group(1))
    match = re.search(r"(\d{1,2})\s*(?:人|位|个)?\s*(?:团队|队伍|小组)", prompt)
    if match:
        return int(match.group(1))
    return None


def _extract_trade_price(prompt: str) -> float | None:
    price_text = _extract_label_value(prompt, ("价格", "预算", "期望价格"))
    if price_text:
        if any(word in price_text for word in ("面议", "可议", "私聊")):
            return None
        number = _extract_first_number(price_text)
        if number is not None:
            return number
    if any(word in prompt for word in ("免费", "白送", "赠送")):
        return 0.0
    match = re.search(r"(\d+(?:\.\d+)?)\s*(?:元|块|rmb|RMB)", prompt)
    if match:
        return float(match.group(1))
    return None


def _extract_trade_condition(prompt: str) -> str:
    direct_condition = re.search(
        r"(\u5168\u65b0|\u51e0\u4e4e\u5168\u65b0|\u672a\u62c6\u5c01|[1-9]\s*\u6210\u65b0|[\u4e00\u4e8c\u4e09\u56db\u4e94\u516d\u4e03\u516b\u4e5d\u5341]\u6210\u65b0)",
        prompt,
    )
    if direct_condition:
        return direct_condition.group(1).replace(" ", "")
    explicit = _extract_label_value(prompt, ("成色", "新旧程度", "商品状况"))
    if explicit:
        return explicit
    match = re.search(r"(全新|几乎全新|未拆封|9成新|8成新|7成新|自用|轻微使用痕迹)", prompt)
    return match.group(1) if match else ""


def _extract_negotiable(prompt: str) -> bool | None:
    clean = _clean_prompt(prompt)
    if any(word in clean for word in ("不议价", "不刀", "谢绝还价", "固定价")):
        return False
    if any(word in clean for word in ("可议价", "可小刀", "小刀", "面议", "能谈", "可谈")):
        return True
    return None


def _extract_skill_list(prompt: str) -> list[str]:
    explicit = _extract_tag_list(prompt, "技能") or _extract_tag_list(prompt, "需要的技能")
    if explicit:
        return explicit
    values: list[str] = []
    for skill in COMMON_SKILLS:
        if skill in prompt:
            values.append(skill)
    return list(dict.fromkeys(values))


def _expand_text_with_agent(intent_label: str, field_label: str, seed_text: str, min_length: int, extra_hint: str = "") -> str:
    clean = _clean_prompt(seed_text)
    if not clean:
        return clean
    messages = [
        {
            "role": "system",
            "content": (
                "你是 CampusClaw 小程序里的写作助手。"
                "请根据用户已有信息，把字段扩写到更适合直接填写到表单里的版本。"
                "保留原意，不要编造脱离原意的设定，不要加解释，只返回字段文本本身。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"目标场景：{intent_label}\n"
                f"目标字段：{field_label}\n"
                f"最低长度：{min_length} 个字\n"
                f"已有信息：{clean}\n"
                f"{extra_hint}\n"
                "请输出一段更完整、更自然、可直接填写的中文文本。"
            ),
        },
    ]
    try:
        result = _clean_prompt(call_agent(messages))
    except AgentCallError:
        result = ""
    if len(result) >= min_length:
        return result
    return ""


def _fallback_expand_text(field_key: str, seed_text: str, min_length: int, fallback: str) -> str:
    clean = _clean_prompt(seed_text)
    if not clean:
        return fallback
    if field_key in {"body", "details", "description", "bio"}:
        expanded = f"{clean}。如果你也对这个方向感兴趣，欢迎继续交流，我也愿意补充更多细节。"
    elif field_key == "summary":
        expanded = f"{clean}，希望找到节奏合适、愿意认真配合的同学一起推进。"
    elif field_key == "headline":
        expanded = f"{clean}，欢迎一起交流和合作。"
    else:
        expanded = clean
    return expanded if len(expanded) >= min_length else (expanded + fallback)[: max(min_length, len(expanded))]


def _looks_like_raw_prompt(value: str, prompt: str) -> bool:
    clean_value = _clean_prompt(value)
    clean_prompt = _clean_prompt(prompt)
    if not clean_value or not clean_prompt:
        return False
    if clean_value == clean_prompt:
        return True
    if clean_value in clean_prompt or clean_prompt in clean_value:
        shorter = min(len(clean_value), len(clean_prompt))
        longer = max(len(clean_value), len(clean_prompt))
        return shorter >= 8 and shorter / max(longer, 1) >= 0.65
    return False


def _ensure_generated_text(
    field_key: str,
    field_label: str,
    seed_text: str,
    source_prompt: str,
    min_length: int,
    fallback: str,
    intent_label: str,
) -> str:
    clean = _clean_prompt(seed_text)
    should_regenerate = len(clean) < min_length or _looks_like_raw_prompt(clean, source_prompt)
    if not should_regenerate:
        return clean
    ai_value = _expand_text_with_agent(
        intent_label,
        field_label,
        clean or source_prompt or fallback,
        min_length,
        "要求：不要照搬用户原话，要整理成自然、完整、适合直接发布的表单内容。",
    )
    if ai_value and not _looks_like_raw_prompt(ai_value, source_prompt):
        return ai_value
    return _fallback_expand_text(field_key, clean or source_prompt or fallback, min_length, fallback)


def _ensure_min_text(field_key: str, field_label: str, seed_text: str, min_length: int, fallback: str, intent_label: str) -> str:
    clean = _clean_prompt(seed_text)
    if len(clean) >= min_length:
        return clean
    ai_value = _expand_text_with_agent(intent_label, field_label, clean or fallback, min_length)
    if ai_value:
        return ai_value
    return _fallback_expand_text(field_key, clean or fallback, min_length, fallback)


def _default_payload_for_kind(kind: str, session, prompt: str) -> dict[str, Any]:
    clean = _clean_prompt(prompt)
    if kind == "forum_post_create":
        return {"title": "", "body": clean, "category": "", "tags": []}
    if kind == "team_post_create":
        return {"title": "", "summary": "", "details": clean, "target_size": None, "tags": [], "required_skills": []}
    if kind == "trade_post_create":
        return {"post_type": "", "title": "", "description": clean, "price": None, "condition": "", "tags": [], "is_negotiable": True}
    if kind == "team_apply":
        return {"post_id": session.context_target_id, "message": clean}
    if kind == "trade_favorite":
        return {"post_id": session.context_target_id}
    if kind == "context_chat_message_send":
        return {
            "target_user_id": session.context_target_id,
            "source_type": session.context_target_type or "",
            "source_id": "",
            "body": clean,
        }
    if kind == "profile_update":
        return {"nickname": "", "headline": "", "bio": clean, "gender": "unknown", "major": "", "grade": "", "interests": []}
    if kind == "forum_comment_create":
        return {"post_id": session.context_target_id, "parent": "", "body": clean}
    if kind == "chat_message_send":
        return {"thread_id": session.context_target_id, "body": clean}
    if kind == "dating_profile_update":
        return {"nickname": "", "gender": "unknown", "height_cm": None, "weight_kg": None, "age": None, "interests": [], "bio": clean, "is_visible": True}
    if kind == "dating_preference_update":
        return {"preferred_genders": [], "preferred_interests": [], "min_height_cm": None, "max_height_cm": None, "min_weight_kg": None, "max_weight_kg": None, "min_age": None, "max_age": None}
    return {"body": clean}


def _intent_for_session(page_type: str, prompt: str) -> str:
    kind = _guess_kind(page_type, prompt)
    clean = _clean_prompt(prompt)
    if _looks_like_dating_request(clean):
        return "dating_setup"
    has_team_signal = any(word in clean for word in TEAM_INTENT_KEYWORDS)
    has_trade_signal = any(word in clean for word in TRADE_OBJECT_KEYWORDS)
    if page_type == "publish" and has_team_signal and not has_trade_signal:
        return "team_post_create"
    if page_type == "publish" and has_team_signal and any(word in clean for word in ("前端", "后端", "目标", "人", "同学", "开发")):
        return "team_post_create"
    if page_type == "publish" and any(word in clean for word in ("申请加入", "申请组队", "加入这个组队", "帮我申请", "报名这个组队")):
        return "team_apply"
    if page_type == "publish" and any(word in clean for word in ("收藏这个交易", "收藏交易", "想收藏", "先收藏")):
        return "trade_favorite"
    if page_type == "publish" and any(word in clean for word in ("联系卖家", "联系对方", "私聊对方", "给对方发消息", "帮我发消息")):
        return "context_chat_message_send"
    if kind == "dating_profile_update":
        return "dating_setup"
    return kind


def _correct_intent_for_prompt(intent: str, page_type: str, prompt: str) -> str:
    clean = _clean_prompt(prompt)
    if _looks_like_dating_request(clean):
        return "dating_setup"
    has_team_signal = any(word in clean for word in TEAM_INTENT_KEYWORDS)
    has_trade_signal = any(word in clean for word in TRADE_OBJECT_KEYWORDS)
    if page_type == "publish" and intent == "trade_post_create" and has_team_signal:
        if not has_trade_signal or any(word in clean for word in ("前端", "后端", "目标", "同学", "开发", "项目")):
            return "team_post_create"
    return intent


def _intent_display(intent: str) -> str:
    mapping = {
        "forum_post_create": "论坛帖子",
        "forum_comment_create": "评论内容",
        "team_post_create": "组队招募",
        "team_apply": "组队申请",
        "trade_post_create": "交易帖子",
        "trade_favorite": "交易收藏",
        "context_chat_message_send": "联系消息",
        "profile_update": "个人资料",
        "chat_message_send": "聊天消息",
        "dating_setup": "恋爱匹配资料",
    }
    return mapping.get(intent, "内容草稿")


def _intent_target_page(intent: str) -> str:
    if intent == "dating_setup":
        return "/pages/dating/index"
    skill = SKILLS.get(intent)
    return skill.target_page if skill else ""


def _get_required_fields(intent: str) -> list[tuple[str, str]]:
    mapping = {
        "forum_post_create": [("title", "帖子标题"), ("body", "帖子正文")],
        "forum_comment_create": [("post_id", "目标帖子"), ("body", "评论内容")],
        "team_post_create": [("title", "招募标题"), ("summary", "一句话概述"), ("details", "详细说明"), ("target_size", "目标人数")],
        "team_apply": [("post_id", "目标招募"), ("message", "申请留言")],
        "trade_post_create": [("post_type", "交易类型"), ("title", "交易标题"), ("description", "交易描述")],
        "trade_favorite": [("post_id", "目标交易")],
        "context_chat_message_send": [("target_user_id", "联系对象"), ("body", "消息内容")],
        "profile_update": [("headline", "一句话介绍"), ("major", "专业"), ("grade", "年级")],
        "chat_message_send": [("thread_id", "聊天对象"), ("body", "消息内容")],
        "dating_setup": [("bio", "自我介绍"), ("preference", "想认识什么样的人")],
    }
    return mapping.get(intent, [])


def _merge_forum_post(payload: dict[str, Any], prompt: str, question_field: str) -> None:
    clean = _clean_prompt(prompt)
    explicit_title = _extract_label_value(prompt, ("标题",))
    explicit_body = _extract_label_value(prompt, ("正文", "内容"))
    if explicit_title:
        payload["title"] = explicit_title
    if explicit_body:
        payload["body"] = explicit_body
    if not payload.get("category"):
        for category in FORUM_CATEGORIES:
            if category in clean:
                payload["category"] = category
                break
    if question_field == "title" and clean:
        payload["title"] = clean
    elif question_field == "body" and clean:
        payload["body"] = clean
    elif clean and not explicit_body and not explicit_title:
        if not payload.get("title"):
            payload["title"] = _fallback_title(clean, "想和大家聊聊这件事")
        payload["body"] = clean if len(clean) >= len(_text(payload.get("body"))) else _text(payload.get("body"))
    tags = _extract_tag_list(prompt, "标签")
    if tags:
        payload["tags"] = tags
    if not payload.get("category"):
        payload["category"] = "校园日常"


def _merge_forum_comment(payload: dict[str, Any], prompt: str, question_field: str) -> None:
    clean = _clean_prompt(prompt)
    if question_field == "body" or not payload.get("body"):
        payload["body"] = clean


def _merge_team_post(payload: dict[str, Any], prompt: str, question_field: str) -> None:
    clean = _clean_prompt(prompt)
    explicit_title = _extract_label_value(prompt, ("标题",))
    explicit_summary = _extract_label_value(prompt, ("概述", "摘要", "简介"))
    explicit_details = _extract_label_value(prompt, ("详情", "详细说明", "说明"))
    if explicit_title:
        payload["title"] = explicit_title
    if explicit_summary:
        payload["summary"] = explicit_summary
    if explicit_details:
        payload["details"] = explicit_details
    if question_field and clean:
        payload[question_field] = clean
    if not any((explicit_title, explicit_summary, explicit_details)) and clean:
        if not payload.get("title"):
            payload["title"] = _derive_title(clean, "想找队友一起做项目")
        if not payload.get("summary"):
            payload["summary"] = clean[:40]
        if len(clean) > len(_text(payload.get("details"))):
            payload["details"] = clean
    target_size = _extract_team_target_size(clean)
    if target_size is not None:
        payload["target_size"] = max(2, min(target_size, 20))
    tags = _extract_tag_list(prompt, "标签")
    if tags:
        payload["tags"] = tags
    skills = _extract_skill_list(prompt)
    if skills:
        payload["required_skills"] = skills


def _merge_trade_post(payload: dict[str, Any], prompt: str, question_field: str) -> None:
    clean = _clean_prompt(prompt)
    explicit_title = _extract_label_value(prompt, ("标题",))
    explicit_desc = _extract_label_value(prompt, ("描述", "详情", "说明"))
    if explicit_title:
        payload["title"] = explicit_title
    if explicit_desc:
        payload["description"] = explicit_desc
    if question_field and clean:
        payload[question_field] = clean
    if clean:
        for keyword, post_type in TRADE_TYPE_MAP.items():
            if keyword in clean:
                payload["post_type"] = post_type
                break
        if len(clean) > len(_text(payload.get("description"))):
            payload["description"] = clean
    price = _extract_trade_price(clean)
    if price is not None:
        payload["price"] = price
    condition = _extract_trade_condition(prompt)
    if condition:
        payload["condition"] = condition
    tags = _extract_tag_list(prompt, "标签")
    if tags:
        payload["tags"] = tags
    negotiable = _extract_negotiable(clean)
    if negotiable is not None:
        payload["is_negotiable"] = negotiable


def _merge_team_apply(payload: dict[str, Any], prompt: str, question_field: str) -> None:
    clean = _clean_prompt(prompt)
    if question_field == "message" or not payload.get("message"):
        payload["message"] = clean


def _merge_context_chat_message(payload: dict[str, Any], prompt: str, question_field: str) -> None:
    clean = _clean_prompt(prompt)
    if question_field == "body" or not payload.get("body"):
        payload["body"] = clean


def _merge_profile(payload: dict[str, Any], prompt: str, question_field: str) -> None:
    clean = _clean_prompt(prompt)
    payload["headline"] = _extract_label_value(prompt, ("一句话介绍", "抬头", "标题")) or payload.get("headline", "")
    payload["major"] = _extract_label_value(prompt, ("专业",)) or payload.get("major", "")
    payload["grade"] = _extract_label_value(prompt, ("年级",)) or payload.get("grade", "")
    payload["nickname"] = _extract_label_value(prompt, ("昵称", "名字")) or payload.get("nickname", "")
    if question_field and clean:
        payload[question_field] = clean
    if not payload.get("headline") and clean:
        payload["headline"] = _derive_title(clean, "想认真介绍一下自己")
    if len(clean) > len(_text(payload.get("bio"))):
        payload["bio"] = clean
    gender = _extract_gender(clean)
    if gender:
        payload["gender"] = gender
    interests = _extract_interest_phrase(clean, ("兴趣", "爱好", "喜欢"))
    if interests:
        payload["interests"] = interests


def _merge_chat(payload: dict[str, Any], prompt: str, question_field: str) -> None:
    clean = _clean_prompt(prompt)
    if question_field == "body" or not payload.get("body"):
        payload["body"] = clean


def _merge_dating_setup(payload: dict[str, Any], prompt: str, question_field: str) -> None:
    clean = _clean_prompt(prompt)
    profile = payload.setdefault("profile", _default_payload_for_kind("dating_profile_update", None, ""))
    preference = payload.setdefault("preference", _default_payload_for_kind("dating_preference_update", None, ""))
    if question_field == "bio" and clean:
        profile["bio"] = clean
    elif question_field == "preference" and clean:
        if not preference.get("preferred_interests"):
            preference["preferred_interests"] = _extract_interest_phrase(clean, ("喜欢", "希望对方", "想认识")) or _split_list(clean)
    if clean:
        nickname = _extract_label_value(prompt, ("昵称", "名字", "称呼"))
        if nickname:
            profile["nickname"] = nickname
        gender = _extract_gender(clean)
        if gender:
            profile["gender"] = gender
        age_match = re.search(r"(?:我|本人)?\s*(\d{1,2})岁", clean)
        if age_match:
            profile["age"] = int(age_match.group(1))
        height_match = re.search(r"身高\s*(\d{2,3}(?:\.\d+)?)", clean)
        if height_match:
            profile["height_cm"] = float(height_match.group(1))
        weight_match = re.search(r"体重\s*(\d{2,3}(?:\.\d+)?)", clean)
        if weight_match:
            profile["weight_kg"] = float(weight_match.group(1))
        interests = _extract_interest_phrase(clean, ("兴趣是", "兴趣有", "爱好是", "爱好有", "喜欢"))
        if interests:
            profile["interests"] = interests
        if len(clean) > len(_text(profile.get("bio"))):
            profile["bio"] = clean
        preferred_genders = _extract_preferred_genders(clean)
        if preferred_genders or any(word in clean for word in ("不限", "都可以", "男女都可", "都行")):
            preference["preferred_genders"] = preferred_genders
        preferred_interests = _extract_interest_phrase(clean, ("希望对方喜欢", "想认识", "想找", "希望对方"))
        if preferred_interests:
            preference["preferred_interests"] = preferred_interests
        min_age, max_age = _extract_int_range(clean, "岁")
        if min_age is not None and max_age is not None:
            preference["min_age"] = min_age
            preference["max_age"] = max_age
        min_height, max_height = _extract_int_range(clean, "cm")
        if min_height is not None and max_height is not None:
            preference["min_height_cm"] = float(min_height)
            preference["max_height_cm"] = float(max_height)


def _merge_prompt_into_payload(intent: str, payload: dict[str, Any], prompt: str, question_field: str) -> dict[str, Any]:
    next_payload = deepcopy(payload)
    if intent == "forum_post_create":
        _merge_forum_post(next_payload, prompt, question_field)
    elif intent == "forum_comment_create":
        _merge_forum_comment(next_payload, prompt, question_field)
    elif intent == "team_post_create":
        _merge_team_post(next_payload, prompt, question_field)
    elif intent == "team_apply":
        _merge_team_apply(next_payload, prompt, question_field)
    elif intent == "trade_post_create":
        _merge_trade_post(next_payload, prompt, question_field)
    elif intent == "context_chat_message_send":
        _merge_context_chat_message(next_payload, prompt, question_field)
    elif intent == "profile_update":
        _merge_profile(next_payload, prompt, question_field)
    elif intent == "chat_message_send":
        _merge_chat(next_payload, prompt, question_field)
    elif intent == "dating_setup":
        _merge_dating_setup(next_payload, prompt, question_field)
    return next_payload


def _missing_fields(intent: str, payload: dict[str, Any]) -> tuple[list[str], list[str]]:
    fields = _get_required_fields(intent)
    missing: list[str] = []
    labels: list[str] = []
    if intent == "dating_setup":
        profile = payload.get("profile", {})
        preference = payload.get("preference", {})
        if len(_text(profile.get("bio"))) < 12:
            missing.append("bio")
            labels.append("自我介绍")
        preferred_interests = _clean_string_list(preference.get("preferred_interests"), 8)
        inferred_preferred_interests = _extract_dating_preference_from_prompt(_text(profile.get("bio")))
        preference_ready = bool(
            preference.get("preferred_genders")
            or preferred_interests
            or inferred_preferred_interests
            or preference.get("min_age")
            or preference.get("max_age")
            or preference.get("min_height_cm")
            or preference.get("max_height_cm")
        )
        if not preference_ready:
            missing.append("preference")
            labels.append("想认识什么样的人")
        return missing, labels

    for field, label in fields:
        value = payload.get(field)
        if field == "post_id" and not _text(value):
            missing.append(field)
            labels.append(label)
        elif field == "target_user_id" and not _text(value):
            missing.append(field)
            labels.append(label)
        elif field == "title" and len(_text(value)) < 2:
            missing.append(field)
            labels.append(label)
        elif field == "body" and intent == "forum_post_create" and len(_text(value)) < 4:
            missing.append(field)
            labels.append(label)
        elif field == "summary" and len(_text(value)) < 4:
            missing.append(field)
            labels.append(label)
        elif field == "details" and len(_text(value)) < 8:
            missing.append(field)
            labels.append(label)
        elif field == "target_size":
            try:
                size = int(value)
            except (TypeError, ValueError):
                size = 0
            if size < 2 or size > 20:
                missing.append(field)
                labels.append(label)
        elif field == "description" and len(_text(value)) < 4:
            missing.append(field)
            labels.append(label)
        elif field == "post_type" and _text(value) not in {"sell", "buy", "exchange", "service"}:
            missing.append(field)
            labels.append(label)
        elif field == "headline" and len(_text(value)) < 2:
            missing.append(field)
            labels.append(label)
        elif field == "major" and len(_text(value)) < 2:
            missing.append(field)
            labels.append(label)
        elif field == "grade" and not _text(value):
            missing.append(field)
            labels.append(label)
        elif field == "thread_id" and not _text(value):
            missing.append(field)
            labels.append(label)
        elif field == "body" and intent == "forum_comment_create" and len(_text(value)) < 2:
            missing.append(field)
            labels.append(label)
        elif field == "body" and intent == "chat_message_send" and len(_text(value)) < 1:
            missing.append(field)
            labels.append(label)
        elif field == "body" and intent == "context_chat_message_send" and len(_text(value)) < 2:
            missing.append(field)
            labels.append(label)
        elif field == "message" and intent == "team_apply" and len(_text(value)) < 4:
            missing.append(field)
            labels.append(label)
    return missing, labels


def _is_context_blocking(intent: str, missing_fields: list[str]) -> bool:
    blocking_by_intent = {
        "forum_comment_create": {"post_id"},
        "chat_message_send": {"thread_id"},
        "team_apply": {"post_id"},
        "trade_favorite": {"post_id"},
        "context_chat_message_send": {"target_user_id"},
    }
    return any(field in blocking_by_intent.get(intent, set()) for field in missing_fields)


def _build_blocking_message(intent: str, missing_labels: list[str]) -> str:
    joined = "、".join(missing_labels)
    return (
        f"现在还缺少{joined}，这个会直接影响动作落到正确对象上。"
        "你可以先进入对应详情页或聊天页再让我继续，也可以先告诉我想写的内容，我先帮你润色。"
        if intent in {"forum_comment_create", "chat_message_send"}
        else f"现在还缺少这些关键信息：{joined}。"
    )


def _normalize_payload(intent: str, payload: dict[str, Any]) -> dict[str, Any]:
    next_payload = deepcopy(payload)
    if intent == "forum_post_create":
        next_payload["category"] = _text(next_payload.get("category")) or "校园日常"
        if not _text(next_payload.get("title")) or _text(next_payload.get("title")) == _fallback_title(_text(next_payload.get("body")), "想和大家聊聊这件事"):
            next_payload["title"] = _generate_short_title("论坛帖子", _text(next_payload.get("body")), "想和大家聊聊这件事")
        else:
            next_payload["title"] = _ensure_min_text("title", "帖子标题", _text(next_payload.get("title")) or _text(next_payload.get("body")), 4, "想认真和大家聊聊这件事", "论坛帖子")
        next_payload["body"] = _ensure_min_text("body", "帖子正文", _text(next_payload.get("body")), 10, "我想把自己的情况和诉求说清楚，也欢迎大家给我一些建议。", "论坛帖子")
    elif intent == "forum_comment_create":
        next_payload["body"] = _ensure_min_text("body", "评论内容", _text(next_payload.get("body")), 2, "想继续了解一下。", "论坛评论")
    elif intent == "team_post_create":
        next_payload["title"] = _ensure_min_text("title", "招募标题", _text(next_payload.get("title")) or _text(next_payload.get("summary")), 4, "想认真找队友一起合作", "组队招募")
        next_payload["summary"] = _ensure_min_text("summary", "一句话概述", _text(next_payload.get("summary")) or _text(next_payload.get("details")), 8, "想找愿意认真推进这件事的同学一起合作。", "组队招募")
        next_payload["details"] = _ensure_min_text("details", "详细说明", _text(next_payload.get("details")) or _text(next_payload.get("summary")), 20, "目前我已经有了明确方向，希望把目标、分工、节奏和合作方式都提前说清楚。", "组队招募")
        try:
            next_payload["target_size"] = max(2, min(int(next_payload.get("target_size") or 3), 20))
        except (TypeError, ValueError):
            next_payload["target_size"] = 3
    elif intent == "trade_post_create":
        next_payload["post_type"] = _text(next_payload.get("post_type")) or "sell"
        if next_payload.get("is_negotiable") is None:
            next_payload["is_negotiable"] = True
        if not _text(next_payload.get("title")) or _text(next_payload.get("title")) == _fallback_title(_text(next_payload.get("description")), "想发布一条交易信息"):
            next_payload["title"] = _generate_short_title("交易帖子", _text(next_payload.get("description")), "校园交易信息")
        else:
            next_payload["title"] = _ensure_min_text("title", "交易标题", _text(next_payload.get("title")) or _text(next_payload.get("description")), 4, "想发布一条校园交易信息", "交易帖子")
        next_payload["description"] = _ensure_min_text("description", "交易描述", _text(next_payload.get("description")) or _text(next_payload.get("title")), 10, "我会把商品状况、价格预期和交易方式补充清楚，方便有需要的同学联系我。", "交易帖子")
    elif intent == "team_apply":
        next_payload["message"] = _ensure_min_text("message", "申请留言", _text(next_payload.get("message")), 10, "我对这个组队方向很感兴趣，也愿意认真投入时间配合推进，希望进一步沟通是否合适加入。", "组队申请")
    elif intent == "context_chat_message_send":
        next_payload["body"] = _ensure_min_text("body", "联系消息", _text(next_payload.get("body")), 8, "你好，我对你发布的内容很感兴趣，想进一步了解一下具体情况，方便继续聊聊吗？", "联系消息")
    elif intent == "profile_update":
        next_payload["headline"] = _ensure_min_text("headline", "一句话介绍", _text(next_payload.get("headline")) or _text(next_payload.get("bio")), 4, "希望认真介绍自己，也欢迎认识更多同学。", "个人资料")
        next_payload["bio"] = _ensure_min_text("bio", "个人简介", _text(next_payload.get("bio")) or _text(next_payload.get("headline")), 12, "我希望把自己的方向、兴趣和想认识的人说清楚，方便后续交流和合作。", "个人资料")
    elif intent == "chat_message_send":
        next_payload["body"] = _ensure_min_text("body", "聊天消息", _text(next_payload.get("body")), 1, "你好，想和你继续聊聊。", "聊天消息")
    elif intent == "dating_setup":
        next_payload = _repair_dating_payload_from_prompt(next_payload, _text(next_payload.get("profile", {}).get("bio")))
        profile = next_payload.setdefault("profile", {})
        preference = next_payload.setdefault("preference", {})
        profile["bio"] = _generate_dating_bio(
            _text(profile.get("bio")),
            "我想认真认识新的朋友，也愿意把自己的兴趣、相处方式和期待表达清楚。",
        )
        if not profile.get("interests"):
            profile["interests"] = _extract_interest_phrase(_text(profile.get("bio")), ("喜欢", "兴趣", "爱好"))[:4]
        if not preference.get("preferred_interests"):
            preference["preferred_interests"] = [
                keyword for keyword in DATING_PREFERENCE_KEYWORDS if keyword in _text(profile.get("bio"))
            ][:4]
        if not preference.get("preferred_interests"):
            preference["preferred_interests"] = _extract_dating_preference_from_prompt(_text(profile.get("bio")))
        if not preference.get("preferred_interests") and profile.get("interests"):
            preference["preferred_interests"] = profile.get("interests", [])[:4]
        if "preferred_genders" not in preference:
            preference["preferred_genders"] = []
    return next_payload


def _build_preview(intent: str, payload: dict[str, Any]) -> str:
    if intent == "forum_post_create":
        return (
            "我先帮你整理出一版可提交的帖子草稿：\n"
            f"标题：{_text(payload.get('title'))}\n"
            f"分类：{_text(payload.get('category')) or '校园日常'}\n"
            f"正文：{_text(payload.get('body'))}"
        )
    if intent == "forum_comment_create":
        return f"我先帮你整理出一版评论草稿：\n评论：{_text(payload.get('body'))}"
    if intent == "team_post_create":
        return (
            "我先帮你整理出一版组队招募草稿：\n"
            f"标题：{_text(payload.get('title'))}\n"
            f"概述：{_text(payload.get('summary'))}\n"
            f"详情：{_text(payload.get('details'))}\n"
            f"目标人数：{payload.get('target_size') or 3} 人\n"
            f"需要技能：{'、'.join(payload.get('required_skills', [])) or '暂未写明'}"
        )
    if intent == "trade_post_create":
        return (
            "我先帮你整理出一版交易帖子草稿：\n"
            f"类型：{TRADE_TYPE_LABELS.get(_text(payload.get('post_type')), '出售')}\n"
            f"标题：{_text(payload.get('title'))}\n"
            f"描述：{_text(payload.get('description'))}\n"
            f"价格：{('¥' + str(payload.get('price'))) if payload.get('price') not in {None, ''} else '面议'}\n"
            f"成色：{_text(payload.get('condition')) or '暂未写明'}\n"
            f"可议价：{'可以' if payload.get('is_negotiable', True) else '不可以'}"
        )
    if intent == "team_apply":
        return f"我先帮你整理出一版组队申请留言：\n申请内容：{_text(payload.get('message'))}"
    if intent == "trade_favorite":
        return "我已经准备好帮你收藏这条交易信息。"
    if intent == "context_chat_message_send":
        return f"我先帮你整理出一版联系消息：\n消息内容：{_text(payload.get('body'))}"
    if intent == "profile_update":
        return (
            "我先帮你整理出一版个人资料草稿：\n"
            f"一句话介绍：{_text(payload.get('headline'))}\n"
            f"专业：{_text(payload.get('major'))}\n"
            f"年级：{_text(payload.get('grade'))}\n"
            f"个人简介：{_text(payload.get('bio'))}"
        )
    if intent == "dating_setup":
        profile = payload.get("profile", {})
        preference = payload.get("preference", {})
        preferred_gender = "不限" if not preference.get("preferred_genders") else "、".join(preference.get("preferred_genders", []))
        preferred_interests = "、".join(preference.get("preferred_interests", [])) or "暂未写明"
        return (
            "我先帮你整理出一版恋爱匹配草稿：\n"
            f"自我介绍：{_text(profile.get('bio'))}\n"
            f"兴趣标签：{'、'.join(profile.get('interests', [])) or '暂未写明'}\n"
            f"偏好性别：{preferred_gender}\n"
            f"偏好兴趣：{preferred_interests}"
        )
    return f"我先帮你整理出一版草稿：\n{payload}"


def _next_question(intent: str, missing_fields: list[str], missing_labels: list[str]) -> tuple[str, str]:
    if not missing_fields:
        return "", ""
    field = missing_fields[0]
    if intent == "forum_post_create":
        if field == "title":
            return "你想把这条帖子起成什么标题？可以直接给我一句话标题。", field
        return "你想重点写哪些背景、问题和诉求？可以直接把正文思路发给我。", field
    if intent == "forum_comment_create":
        return "你想评论什么内容？可以直接把评论发给我。", field
    if intent == "team_post_create":
        mapping = {
            "title": "这条组队招募的标题你想怎么写？",
            "summary": "你可以先给我一句话概述，说明项目方向和你想找什么样的人。",
            "details": "再补充一下详细说明吧，例如背景、目标、分工和时间安排。",
            "target_size": "你预计这次想找几位队友？给我一个 2 到 20 之间的人数就行。",
        }
        return mapping.get(field, "你可以继续补充组队信息。"), field
    if intent == "trade_post_create":
        mapping = {
            "post_type": "这条交易信息更偏向出售、求购、交换还是服务？",
            "title": "你想给这条交易信息起什么标题？",
            "description": "你可以再补充一下商品状况、来源、价格预期或交易方式。",
        }
        return mapping.get(field, "你可以继续补充交易信息。"), field
    if intent == "team_apply":
        if field == "post_id":
            return "当前我还不知道你具体想申请哪条组队。你可以先在对应组队场景里再让我继续。", field
        return "你想怎么介绍自己、说明为什么适合加入？给我 1 到 2 句就行，我帮你润色成申请留言。", field
    if intent == "trade_favorite":
        return "当前我还不知道你具体想收藏哪条交易。你可以在对应交易场景里再让我继续。", field
    if intent == "context_chat_message_send":
        if field == "target_user_id":
            return "当前我还不知道你具体想联系谁。你可以先进入对应组队或交易场景，再让我帮你起草第一条私信。", field
        return "你想先怎么开场？比如询问价格、时间、合作细节或表达加入兴趣，我帮你整理成自然一点的消息。", field
    if intent == "profile_update":
        mapping = {
            "headline": "先给我一句话介绍吧，让别人一眼知道你是什么方向的人。",
            "major": "你的专业是什么？",
            "grade": "你的年级怎么写更合适？",
        }
        return mapping.get(field, "你可以继续补充资料。"), field
    if intent == "chat_message_send":
        if field == "thread_id":
            return "当前我还不知道你具体要发给哪个聊天对象。你可以先进入具体聊天页，或者告诉我你想发的消息内容，我先帮你润色。", field
        return "你可以直接把想发出的消息内容告诉我。", field
    if intent == "dating_setup":
        if field == "bio":
            return "先告诉我你希望别人怎么认识你吧。你可以用 1 到 2 句话介绍自己的性格、兴趣和相处方式。", field
        return "再告诉我你想认识什么样的人吧。例如性别偏好、年龄范围、兴趣关键词，给我 1 到 2 句就行。", field
    return f"还差这些信息：{'、'.join(missing_labels)}。你可以继续补充。", field


def _build_ready_message(intent: str) -> str:
    return (
        f"现在这版{_intent_display(intent)}的基本信息已经够了。"
        "如果你要我生成 AI 动作建议，我就会把它整理成可执行卡片；"
        "如果你想继续改内容，也可以直接告诉我还想优化哪一部分。"
    )


def _action_kinds_for_intent(intent: str) -> list[str]:
    if intent == "dating_setup":
        return ["dating_profile_update", "dating_preference_update"]
    return [intent]


def _payload_for_kind(intent: str, payload: dict[str, Any], kind: str) -> dict[str, Any]:
    if intent != "dating_setup":
        return deepcopy(payload)
    if kind == "dating_profile_update":
        return deepcopy(payload.get("profile", {}))
    if kind == "dating_preference_update":
        return deepcopy(payload.get("preference", {}))
    return {}


def _build_fill_payload(kind: str, payload: dict[str, Any]) -> dict[str, Any]:
    skill = SKILLS[kind]
    return {key: payload.get(key) for key in skill.fill_keys if key in payload}


def _build_preview_entry(kind: str, payload: dict[str, Any]) -> dict[str, str]:
    body = _text(
        payload.get("body")
        or payload.get("details")
        or payload.get("description")
        or payload.get("bio")
        or payload.get("headline")
        or payload.get("message")
        or payload.get("title")
    )
    return {"action": "AI 已准备好一个可执行动作", "title": SKILLS[kind].title, "body": body}


def build_action_proposals_from_intent(user, session, message, intent: str, payload: dict[str, Any]) -> list[dict[str, Any]]:
    proposal_data: list[dict[str, Any]] = []
    for kind in _action_kinds_for_intent(intent):
        skill = SKILLS[kind]
        kind_payload = _payload_for_kind(intent, payload, kind)
        proposal_data.append(
            {
                "user": user,
                "session": session,
                "message": message,
                "kind": kind,
                "title": skill.title,
                "target_page": skill.target_page,
                "payload": kind_payload,
                "fill_payload": _build_fill_payload(kind, kind_payload),
                "preview": _build_preview_entry(kind, kind_payload),
                "expires_at": timezone.now() + timedelta(hours=2),
            }
        )
    return proposal_data


def _has_confirmable_draft(state: dict[str, Any], intent: str) -> bool:
    return state.get("flow") in {"confirming", "ready"} and _text(state.get("intent")) == intent


def _user_accepts_current_draft(signal: str) -> bool:
    return signal in {"confirm_draft", "request_generate", "self_fill"}


def _can_create_actions(
    state: dict[str, Any],
    intent: str,
    signal: str,
    missing_fields: list[str],
    context_blocked: bool,
) -> bool:
    if missing_fields or context_blocked:
        return False
    if signal in {"request_revision", "cancel", "unclear"}:
        return False
    return _has_confirmable_draft(state, intent) and _user_accepts_current_draft(signal)


def _confirmation_signal_from_fallback(
    wants_generate: bool,
    wants_self_fill: bool,
    is_short_confirmation: bool,
) -> str:
    if wants_self_fill:
        return "self_fill"
    if wants_generate:
        return "request_generate"
    if is_short_confirmation:
        return "confirm_draft"
    return "provide_info"


def _correct_signal_for_prompt(signal: str, prompt: str) -> str:
    clean = _clean_prompt(prompt)
    if len(clean) <= 16 and any(word in clean for word in CASUAL_CONFIRM_WORDS):
        return "confirm_draft"
    if len(clean) <= 16 and any(word in clean for word in NO_REVISION_CONFIRM_WORDS):
        return "confirm_draft"
    return signal


def _safe_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)


def _history_for_agent(history, limit: int = 8) -> list[dict[str, str]]:
    recent = list(history or [])[-limit:]
    items: list[dict[str, str]] = []
    for message in recent:
        role = _text(getattr(message, "role", ""))
        if role not in {"user", "assistant"}:
            continue
        items.append({"role": role, "content": _text(getattr(message, "body", ""))[:800]})
    return items


def _required_field_summary() -> dict[str, list[str]]:
    return {intent: [field for field, _label in _get_required_fields(intent)] for intent in sorted(AGENT_ALLOWED_INTENTS)}


def _new_payload_for_intent(intent: str, session, prompt: str) -> dict[str, Any]:
    if intent == "dating_setup":
        return {
            "profile": _default_payload_for_kind("dating_profile_update", session, prompt),
            "preference": _default_payload_for_kind("dating_preference_update", session, prompt),
        }
    return _default_payload_for_kind(intent, session, prompt)


def _sanitize_nested_dict(value: Any, allowed_fields: set[str]) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return {key: deepcopy(item) for key, item in value.items() if key in allowed_fields}


def _sanitize_payload_patch(intent: str, patch: Any) -> dict[str, Any]:
    if not isinstance(patch, dict):
        return {}
    allowed_fields = AGENT_PAYLOAD_FIELDS.get(intent, set())
    clean: dict[str, Any] = {}
    for key, value in patch.items():
        if key not in allowed_fields:
            continue
        if intent == "dating_setup" and key == "profile":
            nested = _sanitize_nested_dict(value, AGENT_DATING_PROFILE_FIELDS)
            if nested:
                clean[key] = nested
            continue
        if intent == "dating_setup" and key == "preference":
            nested = _sanitize_nested_dict(value, AGENT_DATING_PREFERENCE_FIELDS)
            if nested:
                clean[key] = nested
            continue
        clean[key] = deepcopy(value)
    return clean


def _merge_payload_patch(payload: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    next_payload = deepcopy(payload)
    for key, value in patch.items():
        if isinstance(value, dict) and isinstance(next_payload.get(key), dict):
            nested = deepcopy(next_payload.get(key) or {})
            nested.update(value)
            next_payload[key] = nested
        else:
            next_payload[key] = deepcopy(value)
    return next_payload


def _clean_string_list(value: Any, limit: int = 8) -> list[str]:
    if isinstance(value, list):
        raw_items = value
    else:
        raw_items = re.split(r"[,，、\s]+", _text(value))
    items = [_text(item) for item in raw_items if _text(item)]
    return list(dict.fromkeys(items))[:limit]


def _coerce_optional_float(value: Any) -> float | None:
    if value in {"", None}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _postprocess_generated_patch(intent: str, patch: dict[str, Any]) -> dict[str, Any]:
    clean = deepcopy(patch)
    if intent == "forum_post_create":
        if _text(clean.get("category")) not in FORUM_CATEGORIES:
            clean.pop("category", None)
        if "tags" in clean:
            clean["tags"] = _clean_string_list(clean.get("tags"), 6)
    elif intent == "team_post_create":
        if "target_size" in clean:
            try:
                clean["target_size"] = max(2, min(int(clean.get("target_size") or 3), 20))
            except (TypeError, ValueError):
                clean.pop("target_size", None)
        if "tags" in clean:
            clean["tags"] = _clean_string_list(clean.get("tags"), 6)
        if "required_skills" in clean:
            clean["required_skills"] = _clean_string_list(clean.get("required_skills"), 8)
    elif intent == "trade_post_create":
        if _text(clean.get("post_type")) not in {"sell", "buy", "exchange", "service"}:
            clean.pop("post_type", None)
        if "price" in clean:
            clean["price"] = _coerce_optional_float(clean.get("price"))
        if "is_negotiable" in clean:
            clean["is_negotiable"] = bool(clean.get("is_negotiable"))
        if "tags" in clean:
            clean["tags"] = _clean_string_list(clean.get("tags"), 6)
    elif intent == "dating_setup":
        profile = clean.get("profile")
        if isinstance(profile, dict):
            if "interests" in profile:
                profile["interests"] = _clean_string_list(profile.get("interests"), 8)
            for numeric_field in ("height_cm", "weight_kg", "age"):
                if numeric_field in profile:
                    value = _coerce_optional_float(profile.get(numeric_field))
                    profile[numeric_field] = int(value) if numeric_field == "age" and value is not None else value
        preference = clean.get("preference")
        if isinstance(preference, dict):
            if "preferred_genders" in preference:
                preference["preferred_genders"] = [
                    item for item in _clean_string_list(preference.get("preferred_genders"), 4)
                    if item in {"unknown", "male", "female", "other"}
                ]
            if "preferred_interests" in preference:
                preference["preferred_interests"] = _clean_string_list(preference.get("preferred_interests"), 8)
            for numeric_field in (
                "min_height_cm",
                "max_height_cm",
                "min_weight_kg",
                "max_weight_kg",
                "min_age",
                "max_age",
            ):
                if numeric_field in preference:
                    value = _coerce_optional_float(preference.get(numeric_field))
                    preference[numeric_field] = int(value) if numeric_field.endswith("_age") and value is not None else value
    return clean


def _correct_payload_for_prompt(intent: str, payload: dict[str, Any], prompt: str) -> dict[str, Any]:
    clean_payload = deepcopy(payload)
    clean_prompt = _clean_prompt(prompt)
    if intent == "forum_post_create" and any(word in clean_prompt for word in STUDY_CATEGORY_KEYWORDS):
        clean_payload["category"] = "学习交流"
    if intent == "team_post_create" and not clean_payload.get("target_size"):
        target_size = _extract_team_target_size(clean_prompt)
        if target_size is not None:
            clean_payload["target_size"] = max(2, min(target_size, 20))
    if intent == "trade_post_create":
        if not _text(clean_payload.get("post_type")):
            if any(word in clean_prompt for word in TRADE_BUY_KEYWORDS):
                clean_payload["post_type"] = "buy"
            elif any(word in clean_prompt for word in TRADE_EXCHANGE_KEYWORDS):
                clean_payload["post_type"] = "exchange"
            elif any(word in clean_prompt for word in TRADE_SERVICE_KEYWORDS):
                clean_payload["post_type"] = "service"
            elif any(word in clean_prompt for word in TRADE_SELL_KEYWORDS):
                clean_payload["post_type"] = "sell"
        if not _text(clean_payload.get("description")):
            clean_payload["description"] = clean_prompt
        if not _text(clean_payload.get("title")):
            clean_payload["title"] = _generate_short_title("交易帖子", clean_prompt, "校园交易信息")
        if clean_payload.get("price") in {"", None}:
            price = _extract_trade_price(clean_prompt)
            if price is not None:
                clean_payload["price"] = price
        if not _text(clean_payload.get("condition")):
            condition = _extract_trade_condition(clean_prompt)
            if condition:
                clean_payload["condition"] = condition
        negotiable = _extract_negotiable(clean_prompt)
        if negotiable is not None:
            clean_payload["is_negotiable"] = negotiable
    return clean_payload


def _ensure_generated_payload(intent: str, payload: dict[str, Any], source_prompt: str) -> dict[str, Any]:
    next_payload = deepcopy(payload)
    if intent == "forum_post_create":
        next_payload["body"] = _ensure_generated_text(
            "body",
            "帖子正文",
            _text(next_payload.get("body")),
            source_prompt,
            28,
            "我想把具体时间、地点和诉求说清楚，方便感兴趣的同学一起参与。",
            "论坛帖子",
        )
    elif intent == "team_post_create":
        next_payload["summary"] = _ensure_generated_text(
            "summary",
            "一句话概述",
            _text(next_payload.get("summary")),
            source_prompt,
            12,
            "想找节奏合适、愿意认真推进的同学一起合作。",
            "组队招募",
        )
        next_payload["details"] = _ensure_generated_text(
            "details",
            "详细说明",
            _text(next_payload.get("details")),
            source_prompt,
            40,
            "希望把项目目标、需要的能力、合作节奏和时间安排说清楚，方便同学判断是否合适加入。",
            "组队招募",
        )
    elif intent == "trade_post_create":
        next_payload["description"] = _ensure_generated_text(
            "description",
            "交易描述",
            _text(next_payload.get("description")),
            source_prompt,
            28,
            "我会把物品状态、价格预期和校内交易方式说明清楚，方便有需要的同学联系。",
            "交易帖子",
        )
    elif intent == "profile_update":
        next_payload["bio"] = _ensure_generated_text(
            "bio",
            "个人简介",
            _text(next_payload.get("bio")),
            source_prompt,
            28,
            "我希望把自己的方向、兴趣和期待说清楚，方便后续交流。",
            "个人资料",
        )
    elif intent == "dating_setup":
        profile = next_payload.setdefault("profile", {})
        profile["bio"] = _ensure_generated_text(
            "bio",
            "自我介绍",
            _text(profile.get("bio")),
            source_prompt,
            28,
            "我想认真认识新的朋友，也愿意把自己的兴趣、相处方式和期待表达清楚。",
            "恋爱匹配资料",
        )
    return next_payload


def _apply_session_context(intent: str, payload: dict[str, Any], session) -> dict[str, Any]:
    next_payload = deepcopy(payload)
    target_type = _text(getattr(session, "context_target_type", ""))
    target_id = _text(getattr(session, "context_target_id", ""))
    if intent == "forum_comment_create":
        if target_type in {"forum_post", "post", "forum"} and target_id:
            next_payload["post_id"] = target_id
        elif not target_id:
            next_payload.pop("post_id", None)
    elif intent == "team_apply":
        if target_type == "team_post" and target_id:
            next_payload["post_id"] = target_id
        else:
            next_payload.pop("post_id", None)
    elif intent == "trade_favorite":
        if target_type == "trade_post" and target_id:
            next_payload["post_id"] = target_id
        else:
            next_payload.pop("post_id", None)
    elif intent == "chat_message_send":
        if target_type in {"chat_thread", "thread"} and target_id:
            next_payload["thread_id"] = target_id
        else:
            next_payload.pop("thread_id", None)
    elif intent == "context_chat_message_send":
        if target_type in {"user", "profile"} and target_id:
            next_payload["target_user_id"] = target_id
        else:
            next_payload.pop("target_user_id", None)
        next_payload["source_type"] = target_type
        next_payload["source_id"] = target_id if target_type not in {"user", "profile"} else _text(next_payload.get("source_id"))
    return next_payload


def _validate_agent_decision(decision: dict[str, Any]) -> None:
    required_keys = {
        "intent",
        "user_signal",
        "flow",
        "payload_patch",
        "missing_fields",
        "assistant_reply",
        "should_create_actions",
        "action_intents",
    }
    missing = required_keys - set(decision)
    if missing:
        raise AgentCallError(f"Agent decision missing keys: {', '.join(sorted(missing))}")
    if decision.get("intent") not in AGENT_ALLOWED_INTENTS:
        raise AgentCallError("Agent decision intent is invalid.")
    if decision.get("user_signal") not in AGENT_ALLOWED_SIGNALS:
        raise AgentCallError("Agent decision user_signal is invalid.")
    if decision.get("flow") not in AGENT_ALLOWED_FLOWS:
        raise AgentCallError("Agent decision flow is invalid.")
    if not isinstance(decision.get("payload_patch"), dict):
        raise AgentCallError("Agent decision payload_patch must be an object.")
    if not isinstance(decision.get("missing_fields"), list):
        raise AgentCallError("Agent decision missing_fields must be a list.")
    if not isinstance(decision.get("assistant_reply"), str):
        raise AgentCallError("Agent decision assistant_reply must be a string.")
    if not isinstance(decision.get("should_create_actions"), bool):
        raise AgentCallError("Agent decision should_create_actions must be a boolean.")
    if not isinstance(decision.get("action_intents"), list):
        raise AgentCallError("Agent decision action_intents must be a list.")
    invalid_action_intents = [item for item in decision["action_intents"] if item not in AGENT_ALLOWED_ACTION_INTENTS]
    if invalid_action_intents:
        raise AgentCallError("Agent decision action_intents contains invalid values.")


def _build_agent_decision_messages(session, prompt: str, state: dict[str, Any], history) -> list[dict[str, str]]:
    context = {
        "page_type": getattr(session, "page_type", ""),
        "context_path": getattr(session, "context_path", ""),
        "context_target_type": getattr(session, "context_target_type", ""),
        "context_target_id": getattr(session, "context_target_id", ""),
    }
    instructions = {
        "allowed_intents": sorted(AGENT_ALLOWED_INTENTS),
        "allowed_user_signals": sorted(AGENT_ALLOWED_SIGNALS),
        "allowed_flows": sorted(AGENT_ALLOWED_FLOWS),
        "required_fields": _required_field_summary(),
        "payload_fields": {key: sorted(value) for key, value in AGENT_PAYLOAD_FIELDS.items()},
        "dating_nested_fields": {
            "profile": sorted(AGENT_DATING_PROFILE_FIELDS),
            "preference": sorted(AGENT_DATING_PREFERENCE_FIELDS),
        },
        "policy": [
            "确认语义：不用调整了、不用改了、不需要修改、无需调整、没问题不用改，都表示用户认可当前草稿，应归类为 confirm_draft。",
            "意图纠偏：用户说做小程序、项目、需要前端/后端/队友/目标人数时，通常是 team_post_create；即使项目主题包含“交易”二字，也不是 trade_post_create。",
            "论坛分类纠偏：复习、高数、考试、自习、图书馆、课程、作业等学习场景，category 应为“学习交流”。",
            "新规则优先：AI 只判断用户是否想生成或确认；后端会根据字段完整且用户已确认当前草稿来决定是否允许弹卡片。",
            "执行成卡片、生成卡片、弹卡片、变成卡片、出卡片、就按这个来、好的、嗯嗯，都属于 confirm_draft 或 request_generate。",
            "如果当前还没有展示过草稿，即使用户说直接生成卡片，也不要要求 should_create_actions=true；先让后端展示草稿等待确认。",
            "正常路径由你判断用户这句话的语义，不要依赖固定关键词。",
            "产品策略是确认后生成：草稿确认或用户明确要求生成时 should_create_actions 才能为 true。",
            "信息不足时 flow=collecting，并在 assistant_reply 里自然追问一个最重要的问题。",
            "用户要求改标题、改语气、短一点、自然一点等属于 request_revision，不要生成动作卡片。",
            "不要编造 post_id、thread_id、target_user_id；这些上下文 ID 只能来自 current_context。",
            "dating_setup 可以在 action_intents 中同时返回 dating_profile_update 和 dating_preference_update。",
            "当 flow=confirming 且 should_create_actions=false 时，assistant_reply 只写确认问题或修改建议，不要重复完整草稿，后端会自动展示草稿预览。",
            "assistant_reply 用中文，简洁自然；只输出 JSON，不要 Markdown，不要解释。",
        ],
        "output_schema": {
            "intent": "one allowed intent",
            "user_signal": "one allowed user signal",
            "flow": "collecting|confirming|ready",
            "payload_patch": "object with only allowed fields for the intent",
            "missing_fields": "array of field keys still missing after applying payload_patch",
            "assistant_reply": "string",
            "should_create_actions": "boolean",
            "action_intents": "array of allowed action intents",
        },
    }
    return [
        {
            "role": "system",
            "content": (
                "你是 CampusClaw 小程序的 AI 对话决策器。"
                "你的任务是理解用户本轮话语、当前会话状态和页面上下文，然后输出严格 JSON。"
                "不要输出解释、不要输出 Markdown、不要输出 JSON 之外的任何文本。"
            ),
        },
        {
            "role": "user",
            "content": (
                "decision_instructions="
                f"{_safe_json(instructions)}\n"
                f"current_context={_safe_json(context)}\n"
                f"current_state={_safe_json(state)}\n"
                f"recent_history={_safe_json(_history_for_agent(history))}\n"
                f"user_message={_safe_json(prompt)}"
            ),
        },
    ]


def _build_payload_generation_messages(
    session,
    intent: str,
    prompt: str,
    state: dict[str, Any],
    base_payload: dict[str, Any],
    history,
) -> list[dict[str, str]]:
    context = {
        "page_type": getattr(session, "page_type", ""),
        "context_path": getattr(session, "context_path", ""),
        "context_target_type": getattr(session, "context_target_type", ""),
        "context_target_id": getattr(session, "context_target_id", ""),
    }
    schema = {
        "intent": intent,
        "allowed_fields": sorted(AGENT_PAYLOAD_FIELDS.get(intent, set())),
        "forum_categories": list(FORUM_CATEGORIES),
        "trade_post_types": ["sell", "buy", "exchange", "service"],
        "dating_nested_fields": {
            "profile": sorted(AGENT_DATING_PROFILE_FIELDS),
            "preference": sorted(AGENT_DATING_PREFERENCE_FIELDS),
        },
    }
    return [
        {
            "role": "system",
            "content": (
                "你是 CampusClaw 小程序的表单草稿生成器。"
                "你的任务是根据用户表达、历史消息和已有草稿，生成可直接填入表单的高质量 JSON 字段。"
                "不要机械复制用户原话；标题要自然、具体、适合校园社区。"
                "正文、详情、摘要、自我介绍要在不编造关键事实的前提下扩写到可提交程度。"
                "分类、交易类型、标签、技能由你判断，但必须使用 schema 允许的值。"
                "复习、高数、考试、自习、图书馆、课程、作业等学习场景，论坛分类必须选“学习交流”。"
                "做小程序/项目、需要前端或后端、目标人数、找同学开发，属于组队招募，不要当成交易帖子。"
                "恋爱资料不能编造用户没说过的年龄、身高、体重、性别等事实。"
                "只输出 JSON object，不要 Markdown，不要解释。"
            ),
        },
        {
            "role": "user",
            "content": (
                f"schema={_safe_json(schema)}\n"
                f"current_context={_safe_json(context)}\n"
                f"current_state={_safe_json(state)}\n"
                f"current_payload={_safe_json(base_payload)}\n"
                f"recent_history={_safe_json(_history_for_agent(history))}\n"
                f"user_message={_safe_json(prompt)}"
            ),
        },
    ]


def _generate_payload_patch_with_agent(
    session,
    intent: str,
    prompt: str,
    state: dict[str, Any],
    base_payload: dict[str, Any],
    history,
) -> dict[str, Any]:
    if intent not in PAYLOAD_GENERATION_INTENTS:
        return {}
    raw_patch = call_agent_json(
        _build_payload_generation_messages(session, intent, prompt, state, base_payload, history),
        "assistant_payload_generation",
    )
    if isinstance(raw_patch.get("payload_patch"), dict):
        raw_patch = raw_patch["payload_patch"]
    sanitized_patch = _sanitize_payload_patch(intent, raw_patch)
    final_patch = _postprocess_generated_patch(intent, sanitized_patch)
    _assistant_debug(
        "assistant_debug payload_generation intent=%s prompt=%s raw=%s sanitized=%s final=%s",
        intent,
        prompt,
        _safe_json(raw_patch),
        _safe_json(sanitized_patch),
        _safe_json(final_patch),
    )
    return final_patch


def _is_payload_generation_control_signal(signal: str, prompt: str, state: dict[str, Any], intent: str) -> bool:
    if signal in {"cancel", "unclear"}:
        return True
    if signal in {"confirm_draft", "request_generate", "self_fill"}:
        return _has_confirmable_draft(state, intent) or len(_clean_prompt(prompt)) <= 16
    return False


def plan_turn_with_agent(user, session, prompt: str, history) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    clean_prompt = _clean_prompt(prompt)
    state = _normalize_state(getattr(session, "state", None))
    if not clean_prompt:
        raise AgentCallError("Empty prompt should use fallback handling.")

    decision = call_agent_json(_build_agent_decision_messages(session, clean_prompt, state, history), "assistant_turn_decision")
    _validate_agent_decision(decision)

    intent = _correct_intent_for_prompt(_text(decision["intent"]), session.page_type, clean_prompt)
    previous_intent = _text(state.get("intent"))
    base_payload = deepcopy(state.get("collected_payload") or {})
    if not base_payload or (previous_intent and previous_intent != intent and decision["user_signal"] == "new_request"):
        base_payload = _new_payload_for_intent(intent, session, clean_prompt)

    signal = _correct_signal_for_prompt(_text(decision.get("user_signal")), clean_prompt)
    patch: dict[str, Any] = {}
    if not _is_payload_generation_control_signal(signal, clean_prompt, state, intent):
        try:
            patch = _generate_payload_patch_with_agent(session, intent, clean_prompt, state, base_payload, history)
        except AgentCallError:
            patch = {}
    if not patch:
        patch = _postprocess_generated_patch(intent, _sanitize_payload_patch(intent, decision.get("payload_patch")))
    payload = _merge_payload_patch(base_payload, patch)
    if not patch and signal not in {"confirm_draft", "request_generate", "self_fill", "cancel"}:
        payload = _merge_prompt_into_payload(intent, payload, clean_prompt, _text(state.get("question_field")))
    payload = _correct_payload_for_prompt(intent, payload, clean_prompt)
    if intent == "dating_setup":
        payload = _repair_dating_payload_from_prompt(payload, clean_prompt)
    if not _is_payload_generation_control_signal(signal, clean_prompt, state, intent):
        payload = _ensure_generated_payload(intent, payload, clean_prompt)
    payload = _apply_session_context(intent, payload, session)
    normalized_payload = _normalize_payload(intent, payload)
    if intent == "dating_setup":
        normalized_payload = _repair_dating_payload_from_prompt(normalized_payload, clean_prompt)
    missing_fields, missing_labels = _missing_fields(intent, normalized_payload)
    context_blocked = _is_context_blocking(intent, missing_fields)
    _assistant_debug(
        "assistant_debug final_turn intent=%s signal=%s prompt=%s patch=%s payload=%s normalized=%s missing=%s labels=%s",
        intent,
        signal,
        clean_prompt,
        _safe_json(patch),
        _safe_json(payload),
        _safe_json(normalized_payload),
        _safe_json(missing_fields),
        _safe_json(missing_labels),
    )

    next_state = _normalize_state(state)
    next_state.update(
        {
            "intent": intent,
            "draft_kind": "dating_profile_update" if intent == "dating_setup" else intent,
            "draft_target_page": _intent_target_page(intent),
            "collected_payload": normalized_payload,
            "missing_fields": missing_fields,
            "missing_field_labels": missing_labels,
            "question_field": missing_fields[0] if missing_fields else "",
        }
    )

    assistant_reply = _text(decision.get("assistant_reply"))
    if missing_fields:
        if context_blocked:
            assistant_reply = _build_blocking_message(intent, missing_labels)
        elif not assistant_reply:
            question, question_field = _next_question(intent, missing_fields, missing_labels)
            next_state["question_field"] = question_field
            assistant_reply = question
        next_state["flow"] = "collecting"
        next_state["last_question"] = assistant_reply
        return assistant_reply, [], next_state

    preview_text = _build_preview(intent, normalized_payload)
    if _user_accepts_current_draft(signal) and not _has_confirmable_draft(state, intent):
        assistant_reply = "我先把信息整理成一版草稿，你看这版是否合适；如果没问题，回复“好的”或“生成卡片”，我再弹出动作卡片。"

    if _can_create_actions(state, intent, signal, missing_fields, context_blocked):
        next_state["flow"] = "ready"
        next_state["last_question"] = ""
        next_state["question_field"] = ""
        return (
            assistant_reply or "好的，我已经把当前内容整理成可执行的 AI 动作建议了。你可以直接执行，或者先填充到页面里再自己微调。",
            build_action_proposals_from_intent(user, session, None, intent, normalized_payload),
            next_state,
        )

    next_state["flow"] = "confirming"
    next_state["expanded_preview"] = preview_text
    next_state["last_question"] = assistant_reply or "我先把信息整理成一版草稿，你看看是否合适；如果可以，我下一步再生成动作建议。"
    return f"{preview_text}\n\n{next_state['last_question']}", [], next_state


def plan_assistant_turn(user, session, prompt: str, history) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    try:
        return plan_turn_with_agent(user, session, prompt, history)
    except AgentCallError:
        return _plan_assistant_turn_fallback(user, session, prompt, history)
        reply, actions, state = _plan_assistant_turn_fallback(user, session, prompt, history)
        if actions:
            state["flow"] = "ready"
            return (
                "我先把当前信息整理好了，不过这次 AI 判断结果不够稳定，所以暂时不直接弹动作卡片。你可以再确认一次，我会继续帮你生成。",
                [],
                state,
            )
        return reply, actions, state


def _plan_assistant_turn_fallback(user, session, prompt: str, history) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
    clean_prompt = _clean_prompt(prompt)
    state = _normalize_state(getattr(session, "state", None))
    action_gate_state = deepcopy(state)

    if not clean_prompt:
        return "你可以直接告诉我你想处理什么，我会先帮你梳理信息，再决定要不要生成动作建议。", [], state

    intent = _correct_intent_for_prompt(state.get("intent") or _intent_for_session(session.page_type, clean_prompt), session.page_type, clean_prompt)
    wants_generate = _wants_generate(clean_prompt)
    wants_self_fill = _wants_self_fill(clean_prompt)
    is_short_confirmation = _is_short_confirmation(clean_prompt)
    is_control_message = wants_generate or wants_self_fill or is_short_confirmation
    payload = deepcopy(state.get("collected_payload") or {})
    if not payload:
        if intent == "dating_setup":
            payload = {
                "profile": _default_payload_for_kind("dating_profile_update", session, clean_prompt),
                "preference": _default_payload_for_kind("dating_preference_update", session, clean_prompt),
            }
        else:
            payload = _default_payload_for_kind(intent, session, clean_prompt)

    should_merge_prompt = not (state.get("flow") in {"confirming", "ready"} and is_control_message)
    if should_merge_prompt:
        payload = _merge_prompt_into_payload(intent, payload, clean_prompt, _text(state.get("question_field")))
        payload = _correct_payload_for_prompt(intent, payload, clean_prompt)
        if intent == "dating_setup":
            payload = _repair_dating_payload_from_prompt(payload, clean_prompt)
        payload = _ensure_generated_payload(intent, payload, clean_prompt)

    missing_fields, missing_labels = _missing_fields(intent, payload)
    normalized_payload = _normalize_payload(intent, payload)
    if intent == "dating_setup":
        normalized_payload = _repair_dating_payload_from_prompt(normalized_payload, clean_prompt)
        missing_fields, missing_labels = _missing_fields(intent, normalized_payload)
    _assistant_debug(
        "assistant_debug fallback_turn intent=%s prompt=%s payload=%s normalized=%s missing=%s labels=%s",
        intent,
        clean_prompt,
        _safe_json(payload),
        _safe_json(normalized_payload),
        _safe_json(missing_fields),
        _safe_json(missing_labels),
    )

    state.update(
        {
            "intent": intent,
            "draft_kind": "dating_profile_update" if intent == "dating_setup" else intent,
            "draft_target_page": _intent_target_page(intent),
            "collected_payload": normalized_payload,
            "missing_fields": missing_fields,
            "missing_field_labels": missing_labels,
        }
    )

    signal = _correct_signal_for_prompt(
        _confirmation_signal_from_fallback(wants_generate, wants_self_fill, is_short_confirmation),
        clean_prompt,
    )
    context_blocked = _is_context_blocking(intent, missing_fields)

    if not missing_fields and (wants_generate or wants_self_fill):
        preview_text = _build_preview(intent, normalized_payload)
        if not _can_create_actions(action_gate_state, intent, signal, missing_fields, context_blocked):
            state["flow"] = "confirming"
            state["expanded_preview"] = preview_text
            state["question_field"] = ""
            state["last_question"] = "我先把信息整理成一版草稿，你看这版是否合适；如果没问题，回复“好的”或“生成卡片”，我再弹出动作卡片。"
            return (f"{preview_text}\n\n{state['last_question']}", [], state)
        state["flow"] = "ready"
        state["question_field"] = ""
        return (
            "好的，我已经把当前信息整理成可执行的 AI 动作建议了。你可以选择直接执行，或者只填充到页面后自己再改。",
            build_action_proposals_from_intent(user, session, None, intent, normalized_payload),
            state,
        )

    if missing_fields and (wants_generate or wants_self_fill):
        if context_blocked:
            state["flow"] = "collecting"
            state["last_question"] = _build_blocking_message(intent, missing_labels)
            return (_build_blocking_message(intent, missing_labels), [], state)
        question, question_field = _next_question(intent, missing_fields, missing_labels)
        state["flow"] = "collecting"
        state["last_question"] = question
        state["question_field"] = question_field
        return (f"还差这些关键信息：{'、'.join(missing_labels)}。\n{question}", [], state)
        state["flow"] = "ready"
        state["question_field"] = ""
        state["last_question"] = ""
        return (
            f"好的，我先按目前已有信息帮你生成一版可继续编辑的动作建议。"
            f"不过还有这些内容建议你到页面里再补齐：{'、'.join(missing_labels)}。",
            build_action_proposals_from_intent(user, session, None, intent, normalized_payload),
            state,
        )

    if missing_fields and not (wants_generate or wants_self_fill):
        question, question_field = _next_question(intent, missing_fields, missing_labels)
        state["flow"] = "collecting"
        state["last_question"] = question
        state["question_field"] = question_field
        return (
            f"我理解你想整理的是{_intent_display(intent)}。目前还差这些基本信息：{'、'.join(missing_labels)}。\n{question}",
            [],
            state,
        )

    preview_text = _build_preview(intent, normalized_payload)

    if state.get("flow") != "confirming" and not missing_fields:
        state["flow"] = "confirming"
        state["expanded_preview"] = preview_text
        state["last_question"] = "这版草稿你觉得合适吗？如果要调整语气、内容重点或细节，可以直接告诉我。"
        state["question_field"] = ""
        return (
            f"{preview_text}\n\n这版草稿我已经先帮你扩写到更适合直接填写的程度了。你觉得合适吗？如果想调整语气、长度或重点，直接告诉我就行。",
            [],
            state,
        )

    if state.get("flow") == "confirming":
        if wants_generate or wants_self_fill:
            if not _can_create_actions(action_gate_state, intent, signal, missing_fields, context_blocked):
                state["expanded_preview"] = preview_text
                state["last_question"] = "我先把信息整理成一版草稿，你看这版是否合适；如果没问题，回复“好的”或“生成卡片”，我再弹出动作卡片。"
                return (f"{preview_text}\n\n{state['last_question']}", [], state)
            state["flow"] = "ready"
            return (
                "好的，我已经按你确认过的版本生成了 AI 动作建议。你可以直接执行，或者先仅填充再自己改。",
                build_action_proposals_from_intent(user, session, None, intent, normalized_payload),
                state,
            )
        if is_short_confirmation:
            if _can_create_actions(action_gate_state, intent, signal, missing_fields, context_blocked):
                state["flow"] = "ready"
                state["last_question"] = ""
                state["question_field"] = ""
                return (
                    "好的，我已经按你确认的版本生成了 AI 动作卡片。",
                    build_action_proposals_from_intent(user, session, None, intent, normalized_payload),
                    state,
                )
            state["expanded_preview"] = preview_text
            state["last_question"] = _build_ready_message(intent)
            return (_build_ready_message(intent), [], state)
        if _wants_revision(clean_prompt) or not is_short_confirmation:
            state["expanded_preview"] = preview_text
            state["last_question"] = "我已经根据你的新要求重新整理了这版草稿。你觉得现在合适吗？"
            return (
                f"{preview_text}\n\n我已经按你刚才的新要求重新整理了一版。你觉得现在合适吗？如果还要改，继续告诉我就行。",
                [],
                state,
            )

    if state.get("flow") == "ready":
        if wants_generate or wants_self_fill or is_short_confirmation:
            return (
                "好的，我已经把动作建议准备好了。你可以直接执行，或者先仅填充到对应页面。",
                build_action_proposals_from_intent(user, session, None, intent, normalized_payload),
                state,
            )
        state["flow"] = "confirming"
        state["expanded_preview"] = preview_text
        return (
            f"{preview_text}\n\n我先按你的新要求重新整理了一版。你看这版是否合适？如果可以，我下一步再给你生成动作建议。",
            [],
            state,
        )

    reply = build_assistant_reply_with_history(session.page_type, clean_prompt, history)
    state["flow"] = "idle"
    state["question_field"] = ""
    state["last_question"] = ""
    return (reply, [], state)
