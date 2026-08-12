from __future__ import annotations

from datetime import timedelta
from decimal import Decimal
import logging
import os
from typing import Any

from django.db.models import Q
from django.utils import timezone

from dating.models import DatingPreference, DatingProfile, DatingSignal
from teammates.models import TeamPost
from trade.models import TradeFavorite, TradePost

from .embeddings import EmbeddingError, vector_similarity_scores


logger = logging.getLogger(__name__)


RECOMMENDATION_KINDS = {"team_recommendations", "dating_recommendations", "trade_recommendations"}
HIGH_RISK_WORDS = ("删除", "拉黑", "解除拉黑", "隐藏会话", "封禁", "审核通过", "绕过确认", "不用确认", "直接执行")
KNOWN_RECOMMENDATION_KEYWORDS = (
    "前端",
    "后端",
    "设计",
    "产品",
    "算法",
    "运营",
    "文案",
    "摄影",
    "拍摄",
    "比赛",
    "项目",
    "AI",
    "校园",
    "键盘",
    "显示器",
    "电脑",
    "耳机",
    "书",
    "书籍",
    "教材",
    "求购",
    "出售",
    "交换",
    "数码",
    "电影",
    "阅读",
    "跑步",
    "篮球",
    "温柔",
    "同年级",
)
GENERIC_TRADE_TAGS = {"交易", "闲置", "商品", "求购", "出售", "交换", "卖家", "买家"}


def _vector_min_similarity() -> float:
    try:
        return max(-1.0, min(1.0, float(os.getenv("AGENT_VECTOR_MIN_SIMILARITY", "0.25"))))
    except ValueError:
        return 0.25


def _semantic_scores(query: str, documents: list[str]) -> list[float] | None:
    try:
        return vector_similarity_scores(query, documents)
    except EmbeddingError as exc:
        logger.info("Vector recommendation unavailable; using rule fallback: %s", exc)
        return None


def _semantic_percentage(similarity: float) -> int:
    return round(max(0.0, min(1.0, similarity)) * 100)


def _combined_vector_score(similarity: float, business_score: int) -> int:
    semantic_score = _semantic_percentage(similarity)
    return max(0, min(100, round(semantic_score * 0.85 + business_score * 0.15)))


def clean_prompt(prompt: str) -> str:
    return " ".join(str(prompt or "").split()).strip()


def is_blocked_prompt(prompt: str) -> bool:
    clean = clean_prompt(prompt)
    return any(word in clean for word in HIGH_RISK_WORDS)


def is_icebreaker_request(prompt: str) -> bool:
    clean = clean_prompt(prompt)
    return any(word in clean for word in ("破冰", "开场白", "第一句话", "联系ta", "联系TA", "打招呼", "私聊")) and any(
        word in clean for word in ("帮我", "生成", "写", "想")
    )


def _profile_terms(user) -> set[str]:
    terms: set[str] = set()
    try:
        profile = user.profile
    except Exception:
        profile = None
    if profile:
        terms.update(str(item).strip() for item in getattr(profile, "interests", []) if str(item).strip())
        for value in (getattr(profile, "major", ""), getattr(profile, "grade", ""), getattr(profile, "headline", "")):
            terms.update(part for part in str(value).replace("，", " ").replace(",", " ").split() if part)
    try:
        dating = user.dating_profile
    except Exception:
        dating = None
    if dating:
        terms.update(str(item).strip() for item in dating.interests if str(item).strip())
    return terms


def _prompt_terms(prompt: str) -> set[str]:
    clean = clean_prompt(prompt)
    separators = ("，", ",", "。", "、", "：", ":", "；", ";", " ", "\n")
    for sep in separators:
        clean = clean.replace(sep, " ")
    return {part.strip() for part in clean.split(" ") if len(part.strip()) >= 2}


def _overlap_score(terms: set[str], values: list[str] | tuple[str, ...] | str) -> int:
    if isinstance(values, str):
        haystack = values
        return sum(1 for term in terms if term and term in haystack)
    value_set = {str(item).strip() for item in values if str(item).strip()}
    return len(terms & value_set) + sum(1 for term in terms for value in value_set if term in value or value in term)


def _recommendation_terms(prompt: str) -> set[str]:
    terms = set(_prompt_terms(prompt))
    clean = clean_prompt(prompt)
    terms.update(keyword for keyword in KNOWN_RECOMMENDATION_KEYWORDS if keyword and keyword in clean)
    stop_words = {
        "推荐",
        "匹配",
        "几个",
        "一些",
        "帮我",
        "给我",
        "看看",
        "智能",
        "合适",
        "组队",
        "队友",
        "交易",
        "恋爱",
        "对象",
        "闲置",
        "商品",
        "求购",
        "出售",
        "交换",
        "卖家",
        "买家",
        "帖子",
        "现成",
        "现成的",
        "一个",
    }
    return {term for term in terms if term not in stop_words}


def _text_hits(terms: set[str], *values: Any) -> list[str]:
    haystack = " ".join(str(value or "") for value in values)
    return list(dict.fromkeys(term for term in terms if term and term in haystack))


def _list_hits(terms: set[str], values: list[str] | tuple[str, ...]) -> list[str]:
    hits: list[str] = []
    for term in terms:
        for value in values:
            clean_value = str(value).strip()
            if term and clean_value and (term in clean_value or clean_value in term):
                hits.append(term)
                break
    return list(dict.fromkeys(hits))


def _explicitly_relaxes_preference(prompt: str) -> bool:
    clean = clean_prompt(prompt)
    return any(word in clean for word in ("不限", "放宽", "都可以", "无所谓", "不限制"))


def _score_label(score: int) -> str:
    return "很推荐" if score >= 70 else "可以看看"


def _user_name(user) -> str:
    return user.nickname or user.full_name or user.claw_id or user.email


def _recommendation_action(
    user,
    session,
    kind: str,
    title: str,
    target_page: str,
    recommendations: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "user": user,
        "session": session,
        "message": None,
        "kind": kind,
        "title": title,
        "target_page": target_page,
        "payload": {"recommendations": recommendations},
        "fill_payload": {},
        "preview": {
            "action": "AI 推荐结果",
            "title": title,
            "body": "我只会推荐数据库里真实存在的内容，选择后再由你确认下一步。",
            "recommendations": recommendations,
        },
        "expires_at": timezone.now() + timedelta(hours=2),
    }


def build_team_recommendations(user, session, prompt: str) -> dict[str, Any] | None:
    prompt_terms = _recommendation_terms(prompt)
    weak_profile_terms = _profile_terms(user)
    posts = list(
        TeamPost.objects.select_related("author")
        .filter(status=TeamPost.Status.OPEN)
        .exclude(author=user)
        .order_by("-is_highlighted", "-bump_score", "-bumped_at", "-created_at")[:30]
    )
    posts = [post for post in posts if post.current_size < post.target_size]
    query = f"组队需求：{clean_prompt(prompt)}。用户背景与兴趣：{'、'.join(sorted(weak_profile_terms)) or '未填写'}"
    documents = [
        (
            f"组队项目：{post.title}。简介：{post.summary}。详情：{post.details}。"
            f"需要技能：{'、'.join(post.required_skills)}。标签：{'、'.join(post.tags)}。"
        )
        for post in posts
    ]
    semantic_scores = _semantic_scores(query, documents)
    items: list[dict[str, Any]] = []
    for index, post in enumerate(posts):
        tag_hits = _list_hits(prompt_terms, post.tags)
        skill_hits = _list_hits(prompt_terms, post.required_skills)
        text_hits = _text_hits(prompt_terms, post.title, post.summary, post.details)
        if semantic_scores is not None:
            similarity = semantic_scores[index]
            if similarity < _vector_min_similarity():
                continue
            business_score = 50
            business_score += min(16, len(skill_hits) * 8)
            business_score += min(12, len(tag_hits) * 6)
            business_score += min(6, _overlap_score(weak_profile_terms, post.tags + post.required_skills) * 2)
            business_score += 8 if post.is_highlighted else 0
            business_score += min(8, int(post.bump_score or 0))
            score = _combined_vector_score(similarity, min(100, business_score))
            match_method = "vector"
        else:
            if prompt_terms and not (tag_hits or skill_hits or text_hits):
                continue
            score = 48
            score += min(28, len(skill_hits) * 12)
            score += min(24, len(tag_hits) * 10)
            score += min(18, len(text_hits) * 6)
            score += min(4, _overlap_score(weak_profile_terms, post.tags + post.required_skills) * 2)
            score += 8 if post.is_highlighted else 0
            score += min(7, int(post.bump_score or 0))
            score = max(0, min(100, score))
            if score < 50:
                continue
            similarity = None
            match_method = "rules"
        reason_terms = list(dict.fromkeys(skill_hits + tag_hits + text_hits))
        items.append(
            {
                "type": "team",
                "post_id": str(post.id),
                "target_user_id": str(post.author_id),
                "title": post.title,
                "subtitle": f"{post.current_size}/{post.target_size} 人 · {_user_name(post.author)}",
                "score": score,
                "score_label": _score_label(score),
                "reason": (
                    f"语义相似度 {_semantic_percentage(similarity)}%，并命中：{'、'.join(reason_terms[:3])}"
                    if similarity is not None and reason_terms
                    else f"语义相似度 {_semantic_percentage(similarity)}%，与本次组队需求较相关"
                    if similarity is not None
                    else f"与你输入的关键词相关：{'、'.join(reason_terms[:3])}"
                    if reason_terms
                    else "这条组队与本次需求相关，且仍在开放招募。"
                ),
                "match_method": match_method,
                "semantic_similarity": round(similarity, 4) if similarity is not None else None,
                "target_page": "/pages/teammates/index",
                "contact_page": f"/pages/chat/index?targetUserId={post.author_id}&sourceType=team_post&sourceId={post.id}",
                "draft": {
                    "kind": "team_apply",
                    "target_page": "/pages/teammates/index",
                    "fill_payload": {
                        "post_id": str(post.id),
                        "message": f"你好，我对「{post.title}」很感兴趣，想了解一下我是否适合加入。",
                    },
                },
            }
        )
    items.sort(key=lambda item: item["score"], reverse=True)
    recommendations = items[:5]
    if not recommendations:
        return None
    return _recommendation_action(user, session, "team_recommendations", "AI 组队推荐", "/pages/teammates/index", recommendations)


def _matches_range(value: float | int | None, minimum: float | int | None, maximum: float | int | None) -> bool:
    if value is None:
        return True
    if minimum is not None and value < minimum:
        return False
    if maximum is not None and value > maximum:
        return False
    return True


def build_dating_recommendations(user, session, prompt: str) -> dict[str, Any] | None:
    preference, _ = DatingPreference.objects.get_or_create(user=user)
    preference_terms = set(preference.preferred_interests or [])
    prompt_terms = _recommendation_terms(prompt)
    terms = preference_terms | prompt_terms
    relax_preference = _explicitly_relaxes_preference(prompt)
    skipped = {str(value) for value in DatingSignal.objects.filter(actor=user, signal=DatingSignal.Signal.NOT_INTERESTED).values_list("target_id", flat=True)}
    profiles = list(DatingProfile.objects.select_related("user").filter(is_visible=True).exclude(user=user).exclude(user_id__in=skipped)[:50])
    eligible_profiles: list[DatingProfile] = []
    for profile in profiles:
        if not relax_preference and preference.preferred_genders and profile.gender not in preference.preferred_genders:
            continue
        if not relax_preference and not _matches_range(profile.height_cm, preference.min_height_cm, preference.max_height_cm):
            continue
        if not relax_preference and not _matches_range(profile.weight_kg, preference.min_weight_kg, preference.max_weight_kg):
            continue
        if not relax_preference and not _matches_range(profile.age, preference.min_age, preference.max_age):
            continue
        eligible_profiles.append(profile)
    query = (
        f"恋爱匹配需求：{clean_prompt(prompt)}。偏好兴趣：{'、'.join(preference.preferred_interests) or '未填写'}。"
        f"偏好性格：{'、'.join(preference.preferred_personality_types) or '未填写'}。"
    )
    documents = [
        (
            f"候选人昵称：{profile.nickname}。个人介绍：{profile.bio}。兴趣：{'、'.join(profile.interests)}。"
            f"性格：{profile.personality_type}。年龄：{profile.age or '未填写'}。"
        )
        for profile in eligible_profiles
    ]
    semantic_scores = _semantic_scores(query, documents)
    items: list[dict[str, Any]] = []
    for index, profile in enumerate(eligible_profiles):
        preference_overlap = _overlap_score(preference_terms, profile.interests)
        prompt_interest_hits = _list_hits(prompt_terms, profile.interests)
        prompt_text_hits = _text_hits(prompt_terms, profile.nickname, profile.bio)
        if semantic_scores is not None:
            similarity = semantic_scores[index]
            if similarity < _vector_min_similarity():
                continue
            business_score = 55
            business_score += min(24, preference_overlap * 8)
            business_score += min(12, len(prompt_interest_hits) * 6)
            business_score += 6 if profile.personality_type in preference.preferred_personality_types else 0
            business_score += 3 if profile.bio else 0
            score = _combined_vector_score(similarity, min(100, business_score))
            match_method = "vector"
        else:
            score = 54
            score += min(26, preference_overlap * 9)
            score += min(18, len(prompt_interest_hits) * 9)
            score += min(10, len(prompt_text_hits) * 5)
            score += 8 if profile.bio else 0
            score += 5 if profile.nickname else 0
            score = max(0, min(100, score))
            if score < 50:
                continue
            similarity = None
            match_method = "rules"
        common = [item for item in profile.interests if item in terms][:3]
        prompt_common = [item for item in profile.interests if item in prompt_terms][:3]
        items.append(
            {
                "type": "dating",
                "target_user_id": str(profile.user_id),
                "title": profile.nickname or _user_name(profile.user),
                "subtitle": "、".join(profile.interests[:3]) or "校园同学",
                "score": score,
                "score_label": _score_label(score),
                "reason": (
                    f"语义相似度 {_semantic_percentage(similarity)}%，也命中兴趣：{'、'.join(prompt_common)}"
                    if similarity is not None and prompt_common
                    else f"语义相似度 {_semantic_percentage(similarity)}%，符合当前匹配需求"
                    if similarity is not None
                    else f"符合你的偏好，也命中本次关键词：{'、'.join(prompt_common)}"
                    if prompt_common
                    else f"符合你保存的偏好：{'、'.join(common)}"
                    if common
                    else "符合你保存的基础偏好，可以先从资料介绍聊起。"
                ),
                "match_method": match_method,
                "semantic_similarity": round(similarity, 4) if similarity is not None else None,
                "target_page": "/pages/dating/index",
                "contact_page": f"/pages/chat/index?targetUserId={profile.user_id}&sourceType=dating_profile&sourceId={profile.id}",
                "draft": {
                    "kind": "context_chat_message_send",
                    "target_page": "/pages/chat/index",
                    "fill_payload": {
                        "target_user_id": str(profile.user_id),
                        "source_type": "dating_profile",
                        "source_id": str(profile.id),
                        "body": f"你好，我看到你也喜欢{common[0] if common else '校园生活'}，感觉挺有共同话题，想认识一下。",
                    },
                },
            }
        )
    items.sort(key=lambda item: item["score"], reverse=True)
    recommendations = items[:5]
    if not recommendations:
        return None
    return _recommendation_action(user, session, "dating_recommendations", "AI 恋爱推荐", "/pages/dating/index", recommendations)


def build_trade_recommendations(user, session, prompt: str) -> dict[str, Any] | None:
    prompt_terms = _recommendation_terms(prompt)
    weak_profile_terms = _profile_terms(user)
    favorited = set(TradeFavorite.objects.filter(user=user).values_list("post_id", flat=True))
    posts = list(
        TradePost.objects.select_related("author")
        .filter(status=TradePost.Status.OPEN)
        .exclude(author=user)
        .order_by("-is_highlighted", "-bump_score", "-created_at")[:40]
    )
    query = f"校园交易需求：{clean_prompt(prompt)}。用户兴趣与背景：{'、'.join(sorted(weak_profile_terms)) or '未填写'}"
    documents = [
        (
            f"交易类型：{post.get_post_type_display()}。标题：{post.title}。描述：{post.description}。"
            f"成色：{post.condition}。标签：{'、'.join(post.tags)}。价格：{post.price if post.price is not None else '面议'}。"
        )
        for post in posts
    ]
    semantic_scores = _semantic_scores(query, documents)
    items: list[dict[str, Any]] = []
    for index, post in enumerate(posts):
        meaningful_tags = [tag for tag in post.tags if str(tag).strip() not in GENERIC_TRADE_TAGS]
        tag_hits = _list_hits(prompt_terms, meaningful_tags)
        text_hits = _text_hits(prompt_terms, post.title, post.description, post.condition, post.post_type)
        if semantic_scores is not None:
            similarity = semantic_scores[index]
            if similarity < _vector_min_similarity():
                continue
            business_score = 50
            business_score += min(14, len(text_hits) * 7)
            business_score += min(12, len(tag_hits) * 6)
            business_score += min(4, _overlap_score(weak_profile_terms, post.tags) * 2)
            business_score += 8 if post.is_highlighted else 0
            business_score += min(8, int(post.bump_score or 0))
            business_score -= 10 if post.id in favorited else 0
            score = _combined_vector_score(similarity, max(0, min(100, business_score)))
            match_method = "vector"
        else:
            if prompt_terms and not (tag_hits or text_hits):
                continue
            score = 46
            score += min(30, len(text_hits) * 10)
            score += min(24, len(tag_hits) * 10)
            score += min(3, _overlap_score(weak_profile_terms, post.tags) * 1)
            score += 6 if post.is_highlighted else 0
            score += min(6, int(post.bump_score or 0))
            if post.id in favorited:
                score -= 10
            score = max(0, min(100, score))
            if score < 50:
                continue
            similarity = None
            match_method = "rules"
        price = "面议" if post.price is None else f"¥{Decimal(post.price).quantize(Decimal('0.01'))}"
        matched = list(dict.fromkeys(text_hits + tag_hits))[:3]
        items.append(
            {
                "type": "trade",
                "post_id": str(post.id),
                "target_user_id": str(post.author_id),
                "title": post.title,
                "subtitle": f"{price} · {_user_name(post.author)}",
                "score": score,
                "score_label": _score_label(score),
                "reason": (
                    f"语义相似度 {_semantic_percentage(similarity)}%，并命中：{'、'.join(matched)}"
                    if similarity is not None and matched
                    else f"语义相似度 {_semantic_percentage(similarity)}%，与本次交易需求较相关"
                    if similarity is not None
                    else f"与你输入的关键词相关：{'、'.join(matched)}"
                    if matched
                    else "这条交易与本次需求相关，适合先咨询。"
                ),
                "match_method": match_method,
                "semantic_similarity": round(similarity, 4) if similarity is not None else None,
                "target_page": "/pages/trade/index",
                "contact_page": f"/pages/chat/index?targetUserId={post.author_id}&sourceType=trade_post&sourceId={post.id}",
                "draft": {
                    "kind": "context_chat_message_send",
                    "target_page": "/pages/chat/index",
                    "fill_payload": {
                        "target_user_id": str(post.author_id),
                        "source_type": "trade_post",
                        "source_id": str(post.id),
                        "body": f"你好，我看到你发布的「{post.title}」，想了解一下还在吗？",
                    },
                },
            }
        )
    items.sort(key=lambda item: item["score"], reverse=True)
    recommendations = items[:5]
    if not recommendations:
        return None
    return _recommendation_action(user, session, "trade_recommendations", "AI 交易推荐", "/pages/trade/index", recommendations)


def build_recommendation_action(
    user,
    session,
    prompt: str,
    kind: str,
    assistant_reply: str = "",
) -> tuple[str, list[dict[str, Any]], dict[str, Any]] | None:
    if is_blocked_prompt(prompt):
        return ("这些操作风险比较高，我不能替你删除、拉黑、隐藏会话或绕过确认执行。", [], {"flow": "idle"})
    if kind not in RECOMMENDATION_KINDS:
        return None
    builders = {
        "team_recommendations": build_team_recommendations,
        "dating_recommendations": build_dating_recommendations,
        "trade_recommendations": build_trade_recommendations,
    }
    builder = builders.get(kind)
    if not builder:
        return None
    action = builder(user, session, prompt)
    if not action:
        return ("我暂时没有找到足够合适的真实推荐。你可以换个更具体的关键词再试试。", [], {"flow": "idle"})
    reply = assistant_reply.strip() or "我从当前真实数据里挑了几项更合适的推荐，并给了推荐指数。你可以先看看，再选择联系或填充下一步。"
    return (reply, [action], {"flow": "ready", "intent": kind})


def build_icebreaker_action(user, session, prompt: str) -> tuple[str, list[dict[str, Any]], dict[str, Any]] | None:
    if not is_icebreaker_request(prompt):
        return None
    target_user_id = session.context_target_id if session.context_target_type in {"user", "dating_profile"} else ""
    source_type = session.context_target_type or "direct"
    source_id = session.context_target_id or ""
    target_name = "同学"
    if session.context_target_type == "team_post" and session.context_target_id:
        post = TeamPost.objects.filter(id=session.context_target_id).select_related("author").first()
        if post:
            target_user_id = str(post.author_id)
            source_type = "team_post"
            source_id = str(post.id)
            target_name = _user_name(post.author)
            body = f"你好，我看到你发的「{post.title}」，感觉方向挺契合。我想了解一下现在还缺什么角色，我可以先简单介绍下自己。"
        else:
            body = "你好，我看到你的内容感觉挺感兴趣，想了解一下是否方便聊聊。"
    elif session.context_target_type == "trade_post" and session.context_target_id:
        post = TradePost.objects.filter(id=session.context_target_id).select_related("author").first()
        if post:
            target_user_id = str(post.author_id)
            source_type = "trade_post"
            source_id = str(post.id)
            target_name = _user_name(post.author)
            body = f"你好，我看到你发布的「{post.title}」，想问下现在还在吗？如果方便的话我想了解一下细节。"
        else:
            body = "你好，我看到你的交易信息，想了解一下是否还在。"
    else:
        body = "你好，我看到你的资料/内容感觉挺有共同话题，想认识一下，方便聊聊吗？"

    if not target_user_id:
        return ("我可以帮你写破冰消息，不过需要先在某个帖子、交易或候选人页面打开 AI，这样才能知道要联系谁。", [], {"flow": "idle"})
    action = {
        "user": user,
        "session": session,
        "message": None,
        "kind": "context_chat_message_send",
        "title": "AI 联系破冰",
        "target_page": "/pages/chat/index",
        "payload": {"target_user_id": target_user_id, "source_type": source_type, "source_id": source_id, "body": body},
        "fill_payload": {"target_user_id": target_user_id, "source_type": source_type, "source_id": source_id, "body": body},
        "preview": {"action": "AI 已准备好联系破冰消息", "title": f"联系 {target_name}", "body": body},
        "expires_at": timezone.now() + timedelta(hours=2),
    }
    return ("我帮你写了一句更自然的联系开场白。建议先仅填充到聊天框，你再按自己的语气微调。", [action], {"flow": "ready", "intent": "context_chat_message_send"})
