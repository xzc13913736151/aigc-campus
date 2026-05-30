from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from decimal import Decimal, InvalidOperation
from typing import Any, Callable

from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied, ValidationError

from chat.models import ChatMessage, ChatThread
from dating.models import DatingPreference, DatingProfile, DatingSignal
from forum.models import ForumComment, ForumCommentLike, ForumPost, ForumPostLike
from moderation.services import is_blocked_pair
from profiles.serializers import ProfileSerializer
from teammates.models import TeamApplication, TeamPost
from trade.models import TradeFavorite, TradePost


User = get_user_model()


@dataclass(frozen=True)
class Skill:
    kind: str
    title: str
    target_page: str
    fill_keys: tuple[str, ...]
    execute: Callable[[Any, dict[str, Any]], dict[str, Any]]


def _text(value: Any, fallback: str = "") -> str:
    return str(value or fallback).strip()


def _required_text(payload: dict[str, Any], key: str, label: str, min_length: int = 1) -> str:
    value = _text(payload.get(key))
    if len(value) < min_length:
        raise ValidationError(f"{label}不能为空")
    return value


def _list(value: Any) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    return [item.strip() for item in str(value or "").split(",") if item.strip()]


def _optional_float(value: Any, label: str) -> float | None:
    if value in {"", None}:
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{label}格式不正确")


def _optional_decimal(value: Any, label: str) -> Decimal | None:
    if value in {"", None}:
        return None
    try:
        return Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError):
        raise ValidationError(f"{label}格式不正确")


def _preview(title: str, body: str, action: str) -> dict[str, str]:
    return {"action": action, "title": title, "body": body}


def _result(page: str, message: str, **extra: Any) -> dict[str, Any]:
    return {"target_page": page, "message": message, **extra}


def _canonical_thread_users(first, second):
    return (first, second) if str(first.id) < str(second.id) else (second, first)


def execute_forum_post_create(user, payload: dict[str, Any]) -> dict[str, Any]:
    title = _required_text(payload, "title", "帖子标题", 4)
    body = _required_text(payload, "body", "帖子正文", 10)
    post = ForumPost.objects.create(
        author=user,
        title=title[:160],
        body=body,
        category=_text(payload.get("category"), "校园日常")[:80],
        tags=_list(payload.get("tags")),
    )
    return _result(f"/pages/forum/detail?id={post.id}", "帖子已发布", id=str(post.id))


def execute_forum_comment_create(user, payload: dict[str, Any]) -> dict[str, Any]:
    post = get_object_or_404(ForumPost, pk=payload.get("post_id"), is_deleted=False)
    parent_id = payload.get("parent")
    parent = get_object_or_404(ForumComment, pk=parent_id, post=post) if parent_id else None
    comment = ForumComment.objects.create(
        post=post,
        parent=parent,
        author=user,
        body=_required_text(payload, "body", "评论内容", 2),
    )
    return _result(f"/pages/forum/detail?id={post.id}", "评论已发布", id=str(comment.id), post_id=str(post.id))


def execute_forum_post_like(user, payload: dict[str, Any]) -> dict[str, Any]:
    post = get_object_or_404(ForumPost, pk=payload.get("post_id"), is_deleted=False)
    like, created = ForumPostLike.objects.get_or_create(post=post, user=user)
    if not created:
        like.delete()
    return _result(f"/pages/forum/detail?id={post.id}", "帖子点赞状态已更新", liked=created, like_count=post.likes.count())


def execute_forum_comment_like(user, payload: dict[str, Any]) -> dict[str, Any]:
    comment = get_object_or_404(ForumComment, pk=payload.get("comment_id"))
    like, created = ForumCommentLike.objects.get_or_create(comment=comment, user=user)
    if not created:
        like.delete()
    return _result(f"/pages/forum/detail?id={comment.post_id}", "评论点赞状态已更新", liked=created, like_count=comment.likes.count())


def execute_team_post_create(user, payload: dict[str, Any]) -> dict[str, Any]:
    target_size = int(payload.get("target_size") or 3)
    post = TeamPost.objects.create(
        author=user,
        title=_required_text(payload, "title", "招募标题", 4)[:120],
        summary=_required_text(payload, "summary", "招募摘要", 4)[:200],
        details=_required_text(payload, "details", "招募详情", 10),
        target_size=max(2, min(target_size, 20)),
        tags=_list(payload.get("tags")),
        required_skills=_list(payload.get("required_skills")),
    )
    return _result("/pages/teammates/index", "组队招募已发布", id=str(post.id))


def execute_team_apply(user, payload: dict[str, Any]) -> dict[str, Any]:
    post = get_object_or_404(TeamPost, pk=payload.get("post_id"))
    if post.author_id == user.id:
        raise PermissionDenied("不能申请加入自己发起的组队")
    application, created = TeamApplication.objects.get_or_create(
        post=post,
        applicant=user,
        defaults={"message": _text(payload.get("message"), "我对这个组队很感兴趣，希望加入。")[:240]},
    )
    return _result("/pages/teammates/index", "组队申请已提交" if created else "你已经申请过这个组队", id=str(application.id))


def execute_trade_post_create(user, payload: dict[str, Any]) -> dict[str, Any]:
    post_type = _text(payload.get("post_type"), TradePost.PostType.SELL)
    if post_type not in TradePost.PostType.values:
        raise ValidationError("交易类型不正确")
    post = TradePost.objects.create(
        author=user,
        post_type=post_type,
        title=_required_text(payload, "title", "交易标题", 4)[:120],
        description=_required_text(payload, "description", "交易描述", 10),
        price=_optional_decimal(payload.get("price"), "价格"),
        condition=_text(payload.get("condition"))[:40],
        tags=_list(payload.get("tags")),
        is_negotiable=bool(payload.get("is_negotiable", True)),
    )
    return _result("/pages/trade/index", "交易帖子已发布", id=str(post.id))


def execute_trade_favorite(user, payload: dict[str, Any]) -> dict[str, Any]:
    post = get_object_or_404(TradePost, pk=payload.get("post_id"))
    if post.author_id == user.id:
        raise PermissionDenied("不能收藏自己发布的交易")
    favorite, _ = TradeFavorite.objects.get_or_create(user=user, post=post)
    return _result("/pages/trade/index", "交易帖子已收藏", id=str(favorite.id), post_id=str(post.id))


def execute_context_chat_message_send(user, payload: dict[str, Any]) -> dict[str, Any]:
    target = get_object_or_404(User, pk=payload.get("target_user_id"))
    if target.id == user.id:
        raise ValidationError("不能给自己发消息")
    if is_blocked_pair(user, target):
        raise PermissionDenied("当前无法联系该用户")

    user_a, user_b = _canonical_thread_users(user, target)
    thread, _ = ChatThread.objects.get_or_create(
        user_a=user_a,
        user_b=user_b,
        defaults={
            "source_type": _text(payload.get("source_type"), "direct")[:30],
            "source_id": _text(payload.get("source_id"))[:64],
        },
    )
    if _text(payload.get("source_type")) and not thread.source_type:
        thread.source_type = _text(payload.get("source_type"))[:30]
        thread.source_id = _text(payload.get("source_id"))[:64]

    body = _required_text(payload, "body", "消息内容", 1)
    message = ChatMessage.objects.create(thread=thread, sender=user, body=body)
    thread.updated_at = timezone.now()
    thread.hidden_for_user_a = False
    thread.hidden_for_user_b = False
    thread.save(update_fields=["source_type", "source_id", "updated_at", "hidden_for_user_a", "hidden_for_user_b"])
    return _result(
        f"/pages/chat/index?threadId={thread.id}",
        "消息已发送并已建立会话",
        id=str(message.id),
        thread_id=str(thread.id),
    )


def execute_dating_profile_update(user, payload: dict[str, Any]) -> dict[str, Any]:
    profile, _ = DatingProfile.objects.get_or_create(user=user)
    if "nickname" in payload:
        profile.nickname = _text(payload.get("nickname"))[:60]
    if "gender" in payload:
        gender = _text(payload.get("gender"), DatingProfile.Gender.UNKNOWN)
        if gender not in DatingProfile.Gender.values:
            raise ValidationError("性别选项不正确")
        profile.gender = gender
    if "height_cm" in payload:
        profile.height_cm = _optional_float(payload.get("height_cm"), "身高")
    if "weight_kg" in payload:
        profile.weight_kg = _optional_float(payload.get("weight_kg"), "体重")
    if "age" in payload:
        profile.age = payload.get("age") or None
    if "interests" in payload:
        profile.interests = _list(payload.get("interests"))
    if "bio" in payload:
        profile.bio = _text(payload.get("bio"))
    if "is_visible" in payload:
        profile.is_visible = bool(payload.get("is_visible"))
    profile.save()
    return _result("/pages/dating/index", "恋爱匹配展示资料已保存", id=str(profile.id))


def execute_dating_preference_update(user, payload: dict[str, Any]) -> dict[str, Any]:
    preference, _ = DatingPreference.objects.get_or_create(user=user)
    preference.preferred_genders = _list(payload.get("preferred_genders"))
    preference.preferred_interests = _list(payload.get("preferred_interests"))
    preference.min_height_cm = _optional_float(payload.get("min_height_cm"), "最低身高")
    preference.max_height_cm = _optional_float(payload.get("max_height_cm"), "最高身高")
    preference.min_weight_kg = _optional_float(payload.get("min_weight_kg"), "最低体重")
    preference.max_weight_kg = _optional_float(payload.get("max_weight_kg"), "最高体重")
    preference.min_age = payload.get("min_age") or None
    preference.max_age = payload.get("max_age") or None
    preference.preferred_personality_types = []
    preference.save()
    return _result("/pages/dating/index", "匹配偏好已保存", id=str(preference.id))


def execute_dating_signal(user, payload: dict[str, Any]) -> dict[str, Any]:
    target = get_object_or_404(User, pk=payload.get("target_user_id"))
    if target.id == user.id:
        raise ValidationError("不能给自己发送匹配信号")
    signal = _text(payload.get("signal"), DatingSignal.Signal.INTERESTED)
    if signal not in DatingSignal.Signal.values:
        raise ValidationError("匹配信号不正确")
    DatingSignal.objects.update_or_create(actor=user, target=target, defaults={"signal": signal})
    return _result("/pages/dating/index", "匹配信号已发送", target_user_id=str(target.id), signal=signal)


def execute_chat_message_send(user, payload: dict[str, Any]) -> dict[str, Any]:
    thread = get_object_or_404(ChatThread.objects.select_related("user_a", "user_b"), pk=payload.get("thread_id"))
    if user.id not in {thread.user_a_id, thread.user_b_id}:
        raise PermissionDenied("你不是该会话参与者")
    message = ChatMessage.objects.create(thread=thread, sender=user, body=_required_text(payload, "body", "消息内容", 1))
    thread.updated_at = timezone.now()
    thread.hidden_for_user_a = False
    thread.hidden_for_user_b = False
    thread.save(update_fields=["updated_at", "hidden_for_user_a", "hidden_for_user_b"])
    return _result(f"/pages/chat/index?threadId={thread.id}", "消息已发送", id=str(message.id), thread_id=str(thread.id))


def execute_profile_update(user, payload: dict[str, Any]) -> dict[str, Any]:
    profile = user.profile
    serializer = ProfileSerializer(profile, data=payload, partial=True)
    serializer.is_valid(raise_exception=True)
    serializer.save()
    return _result("/pages/profile/index", "个人资料已保存", id=str(profile.id))


SKILLS: dict[str, Skill] = {
    "forum_post_create": Skill("forum_post_create", "发布论坛帖子", "/pages/forum/create", ("title", "body", "category", "tags"), execute_forum_post_create),
    "forum_comment_create": Skill("forum_comment_create", "发布评论", "/pages/forum/detail", ("body", "post_id", "parent"), execute_forum_comment_create),
    "forum_post_like": Skill("forum_post_like", "点赞帖子", "/pages/forum/detail", ("post_id",), execute_forum_post_like),
    "forum_comment_like": Skill("forum_comment_like", "点赞评论", "/pages/forum/detail", ("comment_id",), execute_forum_comment_like),
    "team_post_create": Skill("team_post_create", "发布组队招募", "/pages/teammates/create", ("title", "summary", "details", "target_size", "tags", "required_skills"), execute_team_post_create),
    "team_apply": Skill("team_apply", "申请加入组队", "/pages/teammates/index", ("post_id", "message"), execute_team_apply),
    "trade_post_create": Skill("trade_post_create", "发布交易帖子", "/pages/trade/create", ("title", "description", "price", "post_type", "condition", "tags", "is_negotiable"), execute_trade_post_create),
    "trade_favorite": Skill("trade_favorite", "收藏交易帖子", "/pages/trade/index", ("post_id",), execute_trade_favorite),
    "context_chat_message_send": Skill("context_chat_message_send", "联系对方并发送消息", "/pages/chat/index", ("target_user_id", "source_type", "source_id", "body"), execute_context_chat_message_send),
    "dating_profile_update": Skill("dating_profile_update", "保存恋爱展示资料", "/pages/dating/index", ("nickname", "gender", "height_cm", "weight_kg", "age", "interests", "bio", "is_visible"), execute_dating_profile_update),
    "dating_preference_update": Skill("dating_preference_update", "保存匹配偏好", "/pages/dating/index", ("preferred_genders", "preferred_interests", "min_height_cm", "max_height_cm", "min_weight_kg", "max_weight_kg", "min_age", "max_age"), execute_dating_preference_update),
    "dating_signal": Skill("dating_signal", "发送匹配信号", "/pages/dating/index", ("target_user_id", "signal"), execute_dating_signal),
    "chat_message_send": Skill("chat_message_send", "发送聊天消息", "/pages/chat/index", ("thread_id", "body"), execute_chat_message_send),
    "profile_update": Skill("profile_update", "保存个人资料", "/pages/profile/index", ("nickname", "headline", "bio", "gender", "major", "grade", "interests"), execute_profile_update),
}


def _guess_kind(page_type: str, prompt: str) -> str:
    team_signals = ["小程序", "项目", "前端", "后端", "组队", "招募", "队友", "目标", "开发"]
    trade_signals = ["闲置", "出售", "求购", "交换", "转让", "价格", "元", "面交", "可小刀", "成新"]
    if any(word in prompt for word in team_signals):
        return "team_post_create"
    if any(word in prompt for word in trade_signals) or ("交易" in prompt and not any(word in prompt for word in team_signals)):
        return "trade_post_create"
    if any(word in prompt for word in ["恋爱", "匹配资料", "心动", "偏好"]):
        return "dating_profile_update"
    if any(word in prompt for word in ["聊天", "私聊", "消息"]):
        return "chat_message_send"
    if any(word in prompt for word in ["资料", "简介", "个人介绍"]):
        return "profile_update"
    if any(word in prompt for word in ["评论", "回复评论"]):
        return "forum_comment_create"
    if any(word in prompt for word in ["点赞", "赞一下"]):
        return "forum_post_like"
    if page_type == "messages":
        return "chat_message_send"
    if page_type == "me":
        return "profile_update"
    if page_type == "publish":
        return "team_post_create"
    return "forum_post_create"


def build_action_payload(kind: str, prompt: str, session) -> dict[str, Any]:
    clean = _text(prompt)
    short = clean[:80] or "来自 AI 的内容"
    common_tags = ["AI生成"]
    payloads = {
        "forum_post_create": {"title": short[:36], "body": clean, "category": "校园日常", "tags": common_tags},
        "forum_comment_create": {"post_id": session.context_target_id, "parent": "", "body": clean},
        "forum_post_like": {"post_id": session.context_target_id},
        "forum_comment_like": {"comment_id": session.context_target_id},
        "team_post_create": {"title": short[:36], "summary": short, "details": clean, "target_size": 3, "tags": common_tags, "required_skills": []},
        "team_apply": {"post_id": session.context_target_id, "message": clean},
        "trade_post_create": {"post_type": "sell", "title": short[:36], "description": clean, "price": None, "condition": "", "tags": common_tags, "is_negotiable": True},
        "trade_favorite": {"post_id": session.context_target_id},
        "dating_profile_update": {"nickname": "", "gender": "unknown", "height_cm": None, "weight_kg": None, "age": None, "interests": [], "bio": clean, "is_visible": True},
        "dating_preference_update": {"preferred_genders": [], "preferred_interests": _list(clean), "min_height_cm": None, "max_height_cm": None, "min_weight_kg": None, "max_weight_kg": None, "min_age": None, "max_age": None},
        "dating_signal": {"target_user_id": session.context_target_id, "signal": "interested"},
        "chat_message_send": {"thread_id": session.context_target_id, "body": clean},
        "profile_update": {"headline": short[:120], "bio": clean, "interests": common_tags},
    }
    return payloads.get(kind, payloads["forum_post_create"])


def create_action_proposal(user, session, message, prompt: str):
    kind = _guess_kind(session.page_type, prompt)
    skill = SKILLS[kind]
    payload = build_action_payload(kind, prompt, session)
    fill_payload = {key: payload.get(key) for key in skill.fill_keys if key in payload}
    body = _text(
        payload.get("body")
        or payload.get("details")
        or payload.get("description")
        or payload.get("bio")
        or payload.get("message")
        or payload.get("title")
    )
    return {
        "user": user,
        "session": session,
        "message": message,
        "kind": skill.kind,
        "title": skill.title,
        "target_page": skill.target_page,
        "payload": payload,
        "fill_payload": fill_payload,
        "preview": _preview(skill.title, body, "AI 已准备好一个可执行动作"),
        "expires_at": timezone.now() + timedelta(hours=2),
    }


def execute_action(proposal) -> dict[str, Any]:
    if proposal.status != "pending":
        raise ValidationError("这个 AI 动作已经处理过")
    if proposal.expires_at <= timezone.now():
        proposal.status = "expired"
        proposal.save(update_fields=["status", "updated_at"])
        raise ValidationError("这个 AI 动作已经过期")
    skill = SKILLS.get(proposal.kind)
    if not skill:
        raise ValidationError("不支持的 AI 动作")
    return skill.execute(proposal.user, proposal.payload)
