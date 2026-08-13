from unittest.mock import Mock, call, patch

from django.test import SimpleTestCase

from assistant.agent import AgentCallError, _strip_provider_footer, call_agent


class HiAgentCallTests(SimpleTestCase):
    def test_provider_footer_is_removed_without_losing_answer(self):
        self.assertEqual(_strip_provider_footer("正常回答\n本回答由AI生成，飞书端反馈"), "正常回答")

    @patch("assistant.agent.requests.post")
    def test_call_agent_creates_conversation_then_queries_in_blocking_mode(self, post):
        conversation_response = Mock()
        conversation_response.raise_for_status.return_value = None
        conversation_response.json.return_value = {
            "Conversation": {"AppConversationID": "conversation-123"},
        }
        answer_response = Mock()
        answer_response.raise_for_status.return_value = None
        answer_response.json.return_value = {"event": "message", "answer": "HiAgent answer"}
        post.side_effect = [conversation_response, answer_response]

        with patch.dict(
            "os.environ",
            {
                "HIAGENT_BASE_URL": "https://hiagent.example/api/proxy/api/v1",
                "HIAGENT_API_KEY": "test-key",
                "HIAGENT_USER_ID": "user-001",
            },
            clear=False,
        ):
            answer = call_agent(
                [
                    {"role": "system", "content": "Answer concisely."},
                    {"role": "user", "content": "Hello"},
                ]
            )

        self.assertEqual(answer, "HiAgent answer")
        self.assertEqual(
            post.call_args_list,
            [
                call(
                    "https://hiagent.example/api/proxy/api/v1/create_conversation",
                    headers={"Apikey": "test-key", "Content-Type": "application/json"},
                    json={"UserID": "user-001"},
                    timeout=30,
                ),
                call(
                    "https://hiagent.example/api/proxy/api/v1/chat_query_v2",
                    headers={"Apikey": "test-key", "Content-Type": "application/json"},
                    json={
                        "UserID": "user-001",
                        "AppConversationID": "conversation-123",
                        "Query": "[System]\nAnswer concisely.\n\n[User]\nHello",
                        "ResponseMode": "blocking",
                    },
                    timeout=30,
                ),
            ],
        )

    def test_call_agent_rejects_an_invalid_hiagent_user_id(self):
        with patch.dict(
            "os.environ",
            {
                "HIAGENT_BASE_URL": "https://hiagent.example/api/proxy/api/v1",
                "HIAGENT_API_KEY": "test-key",
                "HIAGENT_USER_ID": "this-user-id-is-too-long",
            },
            clear=False,
        ):
            with self.assertRaisesRegex(AgentCallError, "HIAGENT_USER_ID"):
                call_agent([{"role": "user", "content": "Hello"}])
