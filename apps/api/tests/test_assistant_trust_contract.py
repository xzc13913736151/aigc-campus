from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.exceptions import ValidationError

from assistant.models import AssistantActionProposal, AssistantMessage, AssistantSession
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
def test_content_creation_action_cannot_execute_directly():
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

    with pytest.raises(ValidationError, match="填入原页面"):
        execute_action(proposal)

    assert TradePost.objects.count() == 0
