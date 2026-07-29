from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone

from assistant.models import AssistantActionProposal, AssistantSession
from assistant.orchestrator import (
    _preserve_trade_price_when_unmentioned,
    _repair_trade_price_after_negotiability_reply,
    _resolve_batch_recipients,
    build_assistant_presentation,
)
from assistant.skills import execute_action
from chat.models import ChatMessage, ChatThread


User = get_user_model()


def _thread(first, second):
    user_a, user_b = (first, second) if str(first.id) < str(second.id) else (second, first)
    return ChatThread.objects.create(user_a=user_a, user_b=user_b)


def test_negotiability_choice_does_not_change_price_mode():
    payload = _preserve_trade_price_when_unmentioned(
        {"price": None, "price_mode": ""},
        {"price": None, "price_mode": "negotiable", "is_negotiable": True},
        "可以议价",
    )

    assert payload["price"] is None
    assert payload["price_mode"] == ""
    assert payload["is_negotiable"] is True


def test_negotiability_reply_repairs_stale_face_price_from_old_session():
    payload = _repair_trade_price_after_negotiability_reply(
        {"price": None, "price_mode": "negotiable", "is_negotiable": True},
        "可以议价",
        "我想卖一台二手手机。可以议价",
    )

    assert payload["price"] is None
    assert payload["price_mode"] == ""


def test_binary_options_have_no_custom_and_price_has_no_options():
    presentation = build_assistant_presentation(
        {
            "intent": "trade_post_create",
            "collected_payload": {
                "post_type": "sell",
                "title": "出售手机",
                "description": "出售一台自己的二手手机",
                "price": None,
                "condition": "无",
                "is_negotiable": None,
                "tags": [],
            },
            "missing_fields": [],
        }
    )
    fields = {field["key"]: field for field in presentation["fields"]}

    assert len(fields["is_negotiable"]["options"]) == 2
    assert "custom_prompt" not in fields["is_negotiable"]
    assert "options" not in fields["price"]
    assert [option["value"] for option in fields["condition"]["options"]] == ["全新未拆封", "轻微使用痕迹"]
    assert fields["condition"]["custom_prompt"] == "成色："


@pytest.mark.django_db
def test_recipient_names_resolve_to_existing_contacts():
    sender = User.objects.create_user(email="sender@example.com", password="demo123456")
    first = User.objects.create_user(email="first@example.com", password="demo123456", nickname="张三")
    second = User.objects.create_user(email="second@example.com", password="demo123456", nickname="李四")
    _thread(sender, first)
    _thread(sender, second)

    payload, options = _resolve_batch_recipients(sender, {}, "给张三和李四发消息说今晚八点开会")

    assert set(payload["target_user_ids"]) == {str(first.id), str(second.id)}
    assert set(payload["recipient_names"]) == {"张三", "李四"}
    assert {item["label"] for item in options} == {"张三", "李四"}


@pytest.mark.django_db
def test_confirmed_batch_message_action_sends_to_each_recipient():
    sender = User.objects.create_user(email="batch-sender@example.com", password="demo123456")
    first = User.objects.create_user(email="batch-first@example.com", password="demo123456", nickname="张三")
    second = User.objects.create_user(email="batch-second@example.com", password="demo123456", nickname="李四")
    session = AssistantSession.objects.create(user=sender, page_type="messages")
    proposal = AssistantActionProposal.objects.create(
        user=sender,
        session=session,
        kind="chat_message_batch_send",
        title="发送多人消息",
        payload={
            "target_user_ids": [str(first.id), str(second.id)],
            "recipient_names": ["张三", "李四"],
            "body": "今晚八点开会，请准时参加。",
        },
        expires_at=timezone.now() + timedelta(hours=1),
    )

    result = execute_action(proposal)

    assert result["sent_count"] == 2
    assert set(result["recipient_names"]) == {"张三", "李四"}
    assert ChatMessage.objects.filter(sender=sender, body="今晚八点开会，请准时参加。").count() == 2
    assert ChatThread.objects.filter(user_a=sender).count() + ChatThread.objects.filter(user_b=sender).count() == 2
