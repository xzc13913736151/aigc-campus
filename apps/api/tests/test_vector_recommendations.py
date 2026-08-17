import json
import os
from types import SimpleNamespace
from unittest.mock import Mock, patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import SimpleTestCase, TestCase

from assistant.agent import AgentCallError
from assistant.embeddings import cosine_similarity, embed_texts
from assistant.models import AssistantSession
from assistant.orchestrator import _build_agent_decision_messages, _empty_state, plan_assistant_turn
from assistant.recommendations import (
    build_dating_recommendations,
    build_team_recommendations,
    build_trade_recommendations,
)
from dating.models import DatingProfile
from teammates.models import TeamPost
from trade.models import TradePost


def recommendation_decision(intent: str, query: str) -> dict:
    return {
        "intent": intent,
        "user_signal": "new_request",
        "flow": "ready",
        "payload_patch": {"query": query},
        "missing_fields": [],
        "assistant_reply": "我来查找现有内容。",
        "should_create_actions": True,
        "action_intents": [intent],
    }


class EmbeddingTests(SimpleTestCase):
    def setUp(self):
        cache.clear()

    def test_cosine_similarity_uses_vector_direction(self):
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [1.0, 0.0]), 1.0)
        self.assertAlmostEqual(cosine_similarity([1.0, 0.0], [0.0, 1.0]), 0.0)

    def test_embed_texts_batches_and_caches(self):
        response = Mock()
        response.raise_for_status.return_value = None
        response.json.return_value = {
            "data": [
                {"index": 0, "embedding": [1, 0]},
                {"index": 1, "embedding": [0, 1]},
            ]
        }
        post = Mock(return_value=response)
        environment = {
            "AGENT_EMBEDDING_API_KEY": "test-key",
            "AGENT_EMBEDDING_BASE_URL": "https://ai.example/v1",
            "AGENT_EMBEDDING_MODEL": "embedding-test",
        }
        with patch.dict(os.environ, environment), patch("assistant.embeddings.requests.post", post):
            self.assertEqual(embed_texts(["前端项目", "摄影活动"]), [[1.0, 0.0], [0.0, 1.0]])
            self.assertEqual(embed_texts(["前端项目", "摄影活动"]), [[1.0, 0.0], [0.0, 1.0]])

        self.assertEqual(post.call_count, 1)
        self.assertEqual(post.call_args.args[0], "https://ai.example/v1/embeddings")
        self.assertEqual(
            post.call_args.kwargs["json"],
            {"model": "embedding-test", "input": ["前端项目", "摄影活动"]},
        )


class RecommendationIntentTests(SimpleTestCase):
    def _empty_session(self):
        return SimpleNamespace(
            page_type="general",
            context_path="",
            context_target_type="",
            context_target_id="",
            user=None,
            state={},
        )

    def test_decision_prompt_contains_search_and_publish_examples(self):
        messages = _build_agent_decision_messages(self._empty_session(), "测试输入", _empty_state(), [])
        decisions = [json.loads(message["content"]) for message in messages if message["role"] == "assistant"]

        self.assertEqual(decisions[0]["intent"], "trade_recommendations")
        self.assertEqual(decisions[0]["payload_patch"], {"query": "键盘"})
        self.assertEqual(decisions[2]["intent"], "trade_post_create")
        self.assertEqual(decisions[2]["payload_patch"]["post_type"], "buy")

    def test_ai_failure_does_not_fall_back_to_keyword_routing(self):
        session = self._empty_session()
        with (
            patch("assistant.orchestrator.call_agent_json", side_effect=AgentCallError("offline")),
            patch("assistant.orchestrator.build_recommendation_action") as recommendation_action,
        ):
            reply, actions, state = plan_assistant_turn(None, session, "我想要一个键盘", [])

        recommendation_action.assert_not_called()
        self.assertIn("没有执行任何业务动作", reply)
        self.assertEqual(actions, [])
        self.assertEqual(state, _empty_state())


class VectorRecommendationTests(TestCase):
    def test_team_recommendations_rank_by_vector_similarity(self):
        User = get_user_model()
        requester = User.objects.create_user(email="vector-requester@example.com", password="demo123456")
        design_author = User.objects.create_user(email="vector-design@example.com", password="demo123456")
        sports_author = User.objects.create_user(email="vector-sports@example.com", password="demo123456")
        design_post = TeamPost.objects.create(
            author=design_author,
            title="界面体验优化",
            summary="负责交互流程和视觉呈现",
            details="一起完善页面体验",
            required_skills=["UI设计"],
            tags=["设计"],
        )
        TeamPost.objects.create(
            author=sports_author,
            title="校园篮球训练",
            summary="周末一起训练",
            details="需要热爱体育的同学",
            required_skills=["篮球"],
            tags=["运动"],
        )
        session = AssistantSession.objects.create(user=requester, page_type=AssistantSession.PageType.GENERAL)

        def fake_semantic_scores(_query, documents):
            return [0.92 if "视觉呈现" in document else 0.31 for document in documents]

        with patch("assistant.recommendations._semantic_scores", side_effect=fake_semantic_scores):
            result = build_team_recommendations(requester, session, "找一位懂用户体验的伙伴")

        self.assertIsNotNone(result)
        recommendations = result["preview"]["recommendations"]
        self.assertEqual(recommendations[0]["post_id"], str(design_post.id))
        self.assertEqual(recommendations[0]["match_method"], "vector")
        self.assertAlmostEqual(recommendations[0]["semantic_similarity"], 0.92)

    def test_dating_recommendations_rank_by_vector_similarity(self):
        User = get_user_model()
        requester = User.objects.create_user(email="dating-requester@example.com", password="demo123456")
        photographer = User.objects.create_user(email="dating-photo@example.com", password="demo123456")
        programmer = User.objects.create_user(email="dating-code@example.com", password="demo123456")
        photo_profile = DatingProfile.objects.create(
            user=photographer,
            nickname="光影同学",
            interests=["摄影", "旅行"],
            bio="喜欢用镜头记录校园日常",
            is_visible=True,
        )
        DatingProfile.objects.create(
            user=programmer,
            nickname="代码同学",
            interests=["编程"],
            bio="课余时间研究后端架构",
            is_visible=True,
        )
        session = AssistantSession.objects.create(user=requester, page_type=AssistantSession.PageType.GENERAL)

        def fake_semantic_scores(_query, documents):
            return [0.89 if "镜头记录" in document else 0.33 for document in documents]

        with patch("assistant.recommendations._semantic_scores", side_effect=fake_semantic_scores):
            result = build_dating_recommendations(requester, session, "推荐适合一起记录生活的人")

        self.assertIsNotNone(result)
        recommendations = result["preview"]["recommendations"]
        self.assertEqual(recommendations[0]["target_user_id"], str(photo_profile.user_id))
        self.assertEqual(recommendations[0]["match_method"], "vector")

    def test_trade_recommendations_rank_by_vector_similarity(self):
        User = get_user_model()
        requester = User.objects.create_user(email="trade-requester@example.com", password="demo123456")
        tablet_author = User.objects.create_user(email="trade-tablet@example.com", password="demo123456")
        book_author = User.objects.create_user(email="trade-book@example.com", password="demo123456")
        tablet_post = TradePost.objects.create(
            author=tablet_author,
            title="便携绘画设备",
            description="适合课堂记笔记和创作插画",
            tags=["数码", "绘画"],
        )
        TradePost.objects.create(
            author=book_author,
            title="高等数学教材",
            description="教材和配套习题册",
            tags=["书籍"],
        )
        session = AssistantSession.objects.create(user=requester, page_type=AssistantSession.PageType.GENERAL)

        def fake_semantic_scores(_query, documents):
            return [0.9 if "创作插画" in document else 0.3 for document in documents]

        with patch("assistant.recommendations._semantic_scores", side_effect=fake_semantic_scores):
            result = build_trade_recommendations(requester, session, "推荐能随身画画的东西")

        self.assertIsNotNone(result)
        recommendations = result["preview"]["recommendations"]
        self.assertEqual(recommendations[0]["post_id"], str(tablet_post.id))
        self.assertEqual(recommendations[0]["match_method"], "vector")

    def test_trade_search_correction_leaves_publish_draft(self):
        User = get_user_model()
        requester = User.objects.create_user(email="trade-correction@example.com", password="demo123456")
        seller = User.objects.create_user(email="trade-seller@example.com", password="demo123456")
        earphone_post = TradePost.objects.create(
            author=seller,
            title="无线蓝牙耳机",
            description="自用闲置耳机，功能正常",
            tags=["耳机", "数码"],
        )
        session = AssistantSession.objects.create(
            user=requester,
            page_type=AssistantSession.PageType.GENERAL,
            state={
                "flow": "confirming",
                "intent": "trade_post_create",
                "collected_payload": {
                    "title": "求购闲置耳机",
                    "description": "想找一个闲置耳机",
                    "tags": ["耳机"],
                },
            },
        )

        def fake_semantic_scores(query, documents):
            self.assertIn("耳机", query)
            return [0.91 for _document in documents]

        decision = recommendation_decision("trade_recommendations", "闲置耳机")
        with (
            patch("assistant.orchestrator.call_agent_json", return_value=decision) as agent_call,
            patch("assistant.recommendations._semantic_scores", side_effect=fake_semantic_scores),
        ):
            reply, actions, next_state = plan_assistant_turn(requester, session, "没有现成的卖家吗", [])

        agent_call.assert_called_once()
        self.assertEqual(reply, "我来查找现有内容。")
        self.assertEqual(next_state, {"flow": "ready", "intent": "trade_recommendations"})
        self.assertEqual(actions[0]["kind"], "trade_recommendations")
        self.assertEqual(actions[0]["preview"]["recommendations"][0]["post_id"], str(earphone_post.id))

    def test_rule_fallback_does_not_match_only_generic_trade_words(self):
        User = get_user_model()
        requester = User.objects.create_user(email="trade-fallback@example.com", password="demo123456")
        other_user = User.objects.create_user(email="trade-display@example.com", password="demo123456")
        TradePost.objects.create(
            author=requester,
            title="全新未拆封耳机出售",
            description="自己的闲置耳机",
            tags=["耳机"],
        )
        TradePost.objects.create(
            author=other_user,
            post_type=TradePost.PostType.BUY,
            title="求购二手显示器",
            description="想找一台显示器",
            tags=["显示器", "求购"],
        )
        session = AssistantSession.objects.create(user=requester, page_type=AssistantSession.PageType.GENERAL)

        with patch("assistant.recommendations._semantic_scores", return_value=None):
            result = build_trade_recommendations(requester, session, "帮我找一个闲置的耳机")

        self.assertIsNone(result)

    def test_new_keyboard_search_does_not_reuse_old_earphone_draft(self):
        User = get_user_model()
        requester = User.objects.create_user(email="keyboard-requester@example.com", password="demo123456")
        seller = User.objects.create_user(email="keyboard-seller@example.com", password="demo123456")
        keyboard_post = TradePost.objects.create(
            author=seller,
            title="机械键盘转让",
            description="蓝牙双模机械键盘，功能正常",
            tags=["键盘", "数码"],
        )
        session = AssistantSession.objects.create(
            user=requester,
            page_type=AssistantSession.PageType.PUBLISH,
            state={
                "flow": "confirming",
                "intent": "trade_post_create",
                "collected_payload": {
                    "title": "求购闲置耳机",
                    "description": "想找一个闲置耳机",
                    "tags": ["耳机"],
                },
            },
        )

        def fake_semantic_scores(query, documents):
            self.assertIn("键盘", query)
            self.assertNotIn("耳机", query)
            return [0.93 for _document in documents]

        decision = recommendation_decision("trade_recommendations", "想购买机械键盘")
        with (
            patch("assistant.orchestrator.call_agent_json", return_value=decision) as agent_call,
            patch("assistant.recommendations._semantic_scores", side_effect=fake_semantic_scores),
        ):
            reply, actions, next_state = plan_assistant_turn(requester, session, "我想买一个键盘", [])

        agent_call.assert_called_once()
        self.assertEqual(reply, "我来查找现有内容。")
        self.assertEqual(next_state, {"flow": "ready", "intent": "trade_recommendations"})
        self.assertEqual(actions[0]["preview"]["recommendations"][0]["post_id"], str(keyboard_post.id))
