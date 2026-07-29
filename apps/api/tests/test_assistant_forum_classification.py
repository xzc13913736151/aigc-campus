from types import SimpleNamespace

import pytest

from assistant.orchestrator import (
    _correct_intent_for_prompt,
    _intent_for_session,
    _resolve_forum_category,
    build_assistant_presentation,
)
from forum.categories import FORUM_CATEGORIES, classify_forum_category
from forum.serializers import ForumPostSerializer


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("高数期末应该怎么复习？", "学习交流"),
        ("周六下午操场约人一起打羽毛球", "活动组局"),
        ("求一份暑期实习简历修改建议", "实习求职"),
        ("分享一下我的小程序开发经验和项目复盘", "项目合作"),
        ("项目还缺一个前端队友，想招人组队", "组队招募"),
        ("最近压力很大，想找个地方倾诉一下", "情绪树洞"),
        ("食堂二楼新窗口味道怎么样", "校园日常"),
    ],
)
def test_forum_category_representative_examples(text, expected):
    decision = classify_forum_category(text)

    assert decision["category"] == expected
    assert decision["confidence"] >= 0.8
    assert decision["reason"]


def test_vague_content_has_no_default_category():
    decision = classify_forum_category("hi")

    assert decision["category"] == ""
    assert decision["confidence"] == 0


def test_explicit_category_change_honors_target_after_negation():
    decision = classify_forum_category("这不是学习交流，分类改成项目合作")

    assert decision["category"] == "项目合作"
    assert decision["confidence"] == 1


def test_project_discussion_and_explicit_recruitment_use_different_intents():
    assert _intent_for_session("publish", "想分享我的小程序开发经验") == "forum_post_create"
    assert _intent_for_session("publish", "做小程序还缺一个前端队友") == "team_post_create"


@pytest.mark.parametrize("text", ["找电影搭子", "这周五我想找两个看电影搭子", "明晚约人一起看电影"])
def test_leisure_partner_requests_are_activity_forum_posts(text):
    assert _intent_for_session("publish", text) == "forum_post_create"
    assert _correct_intent_for_prompt("team_post_create", "forum", text) == "forum_post_create"
    assert classify_forum_category(text)["category"] == "活动组局"


@pytest.mark.parametrize("text", ["找前端队友做项目", "项目缺一个后端成员"])
def test_project_member_recruitment_remains_team_post(text):
    assert _intent_for_session("publish", text) == "team_post_create"


def test_user_selected_category_stays_stable_during_later_revision():
    payload, decision, source = _resolve_forum_category(
        {"title": "复习建议", "body": "高数复习经验", "category": "学习交流"},
        "分类改成校园日常",
        "高数复习经验",
        {},
    )
    state = {"classification": decision, "field_sources": {"category": source}}

    revised, revised_decision, revised_source = _resolve_forum_category(
        {**payload, "title": "更自然一点的标题"},
        "标题自然一点",
        "高数复习经验",
        state,
    )

    assert revised["category"] == "校园日常"
    assert revised_decision["source"] == "user"
    assert revised_source == "user"


def test_presentation_marks_category_as_ai_and_exposes_valid_options():
    presentation = build_assistant_presentation(
        {
            "intent": "forum_post_create",
            "collected_payload": {"title": "约羽毛球", "category": "活动组局", "body": "周六操场一起打羽毛球"},
            "missing_fields": [],
            "classification": {
                "category": "活动组局",
                "confidence": 0.92,
                "reason": "包含活动、时间和参与邀请",
                "alternatives": ["校园日常"],
                "source": "ai",
            },
            "field_sources": {"category": "ai"},
        }
    )
    category = next(field for field in presentation["fields"] if field["key"] == "category")

    assert category["source"] == "ai"
    assert category["hint"] == "包含活动、时间和参与邀请"
    assert 1 <= len(category["options"]) <= 2
    assert all(option["value"] in FORUM_CATEGORIES for option in category["options"])
    assert category["custom_prompt"] == "分类改成"


def test_forum_serializer_rejects_unknown_category():
    serializer = ForumPostSerializer(
        data={"title": "测试帖子", "body": "这是一段足够完整的测试正文。", "category": "其他分类", "tags": []}
    )

    assert not serializer.is_valid()
    assert "category" in serializer.errors
