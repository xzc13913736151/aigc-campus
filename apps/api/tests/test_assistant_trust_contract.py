from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from assistant.models import AssistantActionProposal, AssistantMessage, AssistantSession
from assistant.orchestrator import AgentCallError, _correct_intent_for_prompt, plan_assistant_turn
from assistant.serializers import AssistantMessageSerializer
from assistant.skills import execute_action
from trade.models import TradePost


@pytest.mark.django_db
def test_message_presentation_is_persisted_and_serialized():
    user = get_user_model().objects.create_user(email="assistant-presentation@example.com", password="demo123456")
    session = AssistantSession.objects.create(user=user, page_type="publish")
    presentation = {
        "type": "draft",
        "intent": "trade_post_create",
        "title": "交易帖子草稿",
        "fields": [{"key": "is_negotiable", "label": "可议价", "display_value": "未说明", "source": "missing"}],
        "missing_fields": [],
        "suggestions": ["可以议价", "不议价"],
    }
    message = AssistantMessage.objects.create(
        session=session,
        role=AssistantMessage.Role.ASSISTANT,
        body="草稿已整理",
        presentation=presentation,
    )

    restored = AssistantMessage.objects.get(pk=message.pk)
    assert AssistantMessageSerializer(restored).data["presentation"] == presentation


@pytest.mark.django_db
def test_content_creation_action_executes_after_user_confirms_action_card():
    user = get_user_model().objects.create_user(email="assistant-action@example.com", password="demo123456")
    session = AssistantSession.objects.create(user=user, page_type="publish")
    proposal = AssistantActionProposal.objects.create(
        user=user,
        session=session,
        kind="trade_post_create",
        title="发布交易帖子",
        payload={
            "post_type": "sell",
            "title": "出售自用笔记本电脑",
            "description": "个人自用，功能正常，支持校内当面验机交易。",
            "condition": "九成新",
            "is_negotiable": False,
        },
        expires_at=timezone.now() + timedelta(hours=1),
    )

    result = execute_action(proposal)

    assert result["message"] == "交易帖子已发布"
    assert TradePost.objects.count() == 1

    proposal.status = AssistantActionProposal.Status.EXECUTED
    with pytest.raises(ValidationError, match="已经处理过"):
        execute_action(proposal)


@pytest.mark.django_db
def test_complete_forum_draft_immediately_returns_fill_and_publish_action_card(monkeypatch):
    user = get_user_model().objects.create_user(email="assistant-forum-card@example.com", password="demo123456")
    session = AssistantSession.objects.create(user=user, page_type="forum")
    decision = {
        "intent": "forum_post_create",
        "user_signal": "new_request",
        "flow": "ready",
        "payload_patch": {
            "title": "周末图书馆自习组队",
            "category": "学习交流",
            "body": "这周末想在图书馆一起自习，欢迎有相同计划的同学一起交流学习安排。",
        },
        "missing_fields": [],
        "assistant_reply": "我已经整理好这条帖子。",
        "should_create_actions": False,
        "action_intents": [],
    }
    monkeypatch.setattr("assistant.orchestrator.call_agent_json", lambda *_args, **_kwargs: decision)

    reply, actions, state = plan_assistant_turn(user, session, "帮我发一条周末图书馆自习组队帖", [])

    assert reply == "我已经整理好这条帖子。"
    assert state["flow"] == "ready"
    assert len(actions) == 1
    assert actions[0]["kind"] == "forum_post_create"
    assert actions[0]["fill_payload"]["title"] == "周末图书馆自习组队"


def test_explicit_campus_post_request_is_not_routed_as_trade():
    assert _correct_intent_for_prompt("trade_post_create", "general", "帮我写一条校园帖子") == "forum_post_create"


@pytest.mark.django_db
def test_incomplete_draft_names_missing_fields_and_never_returns_action_card(monkeypatch):
    user = get_user_model().objects.create_user(email="assistant-missing@example.com", password="demo123456")
    session = AssistantSession.objects.create(user=user, page_type="publish")
    decision = {
        "intent": "team_post_create",
        "user_signal": "new_request",
        "flow": "collecting",
        "payload_patch": {"title": "招募队友参加比赛"},
        "missing_fields": ["summary", "details", "target_size"],
        "assistant_reply": "我可以先帮你补一版。",
        "should_create_actions": True,
        "action_intents": ["team_post_create"],
    }
    monkeypatch.setattr("assistant.orchestrator.call_agent_json", lambda *_args, **_kwargs: decision)

    reply, actions, state = plan_assistant_turn(user, session, "我要发比赛组队招募", [])

    assert actions == []
    assert state["flow"] == "collecting"
    assert "目标人数" in reply
    assert "还需要" in reply


@pytest.mark.django_db
def test_generic_team_recruitment_request_cannot_be_completed_by_generated_copy(monkeypatch):
    user = get_user_model().objects.create_user(email="assistant-generic-team@example.com", password="demo123456")
    session = AssistantSession.objects.create(user=user, page_type="publish")
    decision = {
        "intent": "team_post_create",
        "user_signal": "new_request",
        "flow": "ready",
        "payload_patch": {
            "title": "比赛组队招募",
            "summary": "寻找志同道合的同学一起参加比赛",
            "details": "希望大家认真参与，按时完成分工并共同推进比赛准备工作。",
            "target_size": 3,
        },
        "missing_fields": [],
        "assistant_reply": "我已经整理好了。",
        "should_create_actions": True,
        "action_intents": ["team_post_create"],
    }
    monkeypatch.setattr("assistant.orchestrator.call_agent_json", lambda *_args, **_kwargs: decision)

    reply, actions, state = plan_assistant_turn(user, session, "帮我发一个比赛组队招募帖", [])

    assert actions == []
    assert state["flow"] == "collecting"
    assert state["question_field"] in {"summary", "details", "target_size"}
    assert "目标人数" in reply


@pytest.mark.django_db
def test_like_request_in_post_context_creates_a_confirmable_like_action(monkeypatch):
    user = get_user_model().objects.create_user(email="assistant-like@example.com", password="demo123456")
    session = AssistantSession.objects.create(
        user=user,
        page_type="forum",
        context_target_type="forum_post",
        context_target_id="post-001",
    )
    decision = {
        "intent": "none",
        "user_signal": "new_request",
        "flow": "ready",
        "payload_patch": {},
        "missing_fields": [],
        "assistant_reply": "好的，我来处理。",
        "should_create_actions": False,
        "action_intents": [],
    }
    monkeypatch.setattr("assistant.orchestrator.call_agent_json", lambda *_args, **_kwargs: decision)

    _reply, actions, state = plan_assistant_turn(user, session, "帮我点赞", [])

    assert state["flow"] == "ready"
    assert len(actions) == 1
    assert actions[0]["kind"] == "forum_post_like"


@pytest.mark.django_db
def test_agent_failure_with_a_complete_draft_asks_for_confirmation_and_confirmation_shows_card(monkeypatch):
    user = get_user_model().objects.create_user(email="assistant-fallback-confirm@example.com", password="demo123456")
    session = AssistantSession.objects.create(
        user=user,
        page_type="publish",
        state={
            "flow": "confirming",
            "intent": "team_post_create",
            "collected_payload": {
                "title": "编程比赛组队",
                "summary": "寻找两位队友参加算法比赛",
                "details": "比赛为期两周，希望队友负责算法和前端展示，每晚线上同步进度。",
                "target_size": 3,
            },
            "missing_fields": [],
            "missing_field_labels": [],
            "question_field": "",
            "field_sources": {"summary": "user", "details": "user", "target_size": "user"},
        },
    )
    monkeypatch.setattr("assistant.orchestrator.call_agent_json", lambda *_args, **_kwargs: (_ for _ in ()).throw(AgentCallError("down")))

    reply, actions, state = plan_assistant_turn(user, session, "确认", [])

    assert actions
    assert actions[0]["kind"] == "team_post_create"
    assert state["flow"] == "ready"
    assert "无法完成意图判断" not in reply
