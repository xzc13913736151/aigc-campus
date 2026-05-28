from __future__ import annotations

from .agent import AgentCallError, call_agent
from .models import AssistantMessage, AssistantSession


PAGE_HINTS = {
    AssistantSession.PageType.FORUM: "你现在在论坛页，我可以帮你润色帖子标题、整理正文结构，或者判断这条内容更适合发讨论帖还是求助帖。",
    AssistantSession.PageType.PUBLISH: "你现在在发布页，我可以帮你判断更适合发帖子、发组队，还是完善恋爱匹配资料。",
    AssistantSession.PageType.MESSAGES: "你现在在消息页，我可以帮你想回复话术、整理沟通重点，或者把想说的话改得更自然。",
    AssistantSession.PageType.ME: "你现在在个人页，我可以帮你润色个人简介、整理标签，或者优化资料展示方式。",
    AssistantSession.PageType.GENERAL: "你可以把当前场景告诉我，我会尽量给你贴近校园社交产品的建议。",
}


def default_session_title(page_type: str) -> str:
    mapping = {
        AssistantSession.PageType.FORUM: "论坛灵感助手",
        AssistantSession.PageType.PUBLISH: "发布策划助手",
        AssistantSession.PageType.MESSAGES: "聊天建议助手",
        AssistantSession.PageType.ME: "资料优化助手",
        AssistantSession.PageType.GENERAL: "CampusClaw AI 助手",
    }
    return mapping.get(page_type, "CampusClaw AI 助手")


def build_assistant_reply(page_type: str, prompt: str) -> str:
    try:
        return build_agent_reply(page_type, prompt)
    except AgentCallError:
        return build_fallback_reply(page_type, prompt)


def build_agent_reply(page_type: str, prompt: str) -> str:
    hint = PAGE_HINTS.get(page_type, PAGE_HINTS[AssistantSession.PageType.GENERAL])
    messages = [
        {
            "role": "system",
            "content": (
                "你是 CampusClaw 小程序里的 AI 助手。"
                "你帮助校园用户写论坛帖子、整理组队招募、优化恋爱匹配资料、润色聊天回复。"
                "回答要具体、自然、中文优先，不要提到你在使用本地模板或演示环境。"
            ),
        },
        {
            "role": "system",
            "content": f"当前页面场景：{hint}",
        },
        {
            "role": "user",
            "content": prompt.strip(),
        },
    ]
    return call_agent(messages, tools=ASSISTANT_TOOLS)


def build_fallback_reply(page_type: str, prompt: str) -> str:
    cleaned_prompt = prompt.strip()
    hint = PAGE_HINTS.get(page_type, PAGE_HINTS[AssistantSession.PageType.GENERAL])
    excerpt = cleaned_prompt[:80]

    if page_type == AssistantSession.PageType.FORUM:
        return f"{hint}\n\n基于你刚才的内容，我建议先明确主题，再给出一个更抓人的开头。如果你愿意，我可以继续帮你把“{excerpt}”整理成可直接发布的帖子。 "
    if page_type == AssistantSession.PageType.PUBLISH:
        return f"{hint}\n\n如果你的目标是快速获得回应，建议先写清楚对象、诉求和时间安排。围绕“{excerpt}”，我可以继续帮你拆成发布文案。 "
    if page_type == AssistantSession.PageType.MESSAGES:
        return f"{hint}\n\n如果你担心回复太生硬，可以先表达态度，再补充细节。针对“{excerpt}”，我可以继续帮你生成几种不同语气的回复。 "
    if page_type == AssistantSession.PageType.ME:
        return f"{hint}\n\n个人资料最重要的是让别人快速知道你是谁、你在找什么。围绕“{excerpt}”，我可以继续帮你润色成更自然的自我介绍。 "
    return f"{hint}\n\n你刚才提到“{excerpt}”。如果你愿意，我可以继续把它拆成更具体的行动建议。 "


def build_assistant_reply_with_history(page_type: str, prompt: str, history: list[AssistantMessage]) -> str:
    try:
        return build_agent_reply_with_history(page_type, prompt, history)
    except AgentCallError:
        return build_fallback_reply(page_type, prompt)


def build_agent_reply_with_history(page_type: str, prompt: str, history: list[AssistantMessage]) -> str:
    hint = PAGE_HINTS.get(page_type, PAGE_HINTS[AssistantSession.PageType.GENERAL])
    messages = [
        {
            "role": "system",
            "content": (
                "你是 CampusClaw 小程序里的 AI 助手。"
                "你帮助校园用户写论坛帖子、整理组队招募、优化恋爱匹配资料、润色聊天回复。"
                "结合历史对话回答，尽量给出可以直接复制或执行的建议。"
            ),
        },
        {
            "role": "system",
            "content": f"当前页面场景：{hint}",
        },
    ]
    messages.extend({"role": item.role, "content": item.body} for item in history)
    messages.append({"role": "user", "content": prompt.strip()})
    return call_agent(messages, tools=ASSISTANT_TOOLS)


ASSISTANT_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "campusclaw_context",
            "description": "CampusClaw product context for forum, teaming, dating, messages and profile pages.",
            "parameters": {
                "type": "object",
                "properties": {
                    "page_type": {
                        "type": "string",
                        "enum": ["forum", "publish", "messages", "me", "general"],
                    },
                    "need": {
                        "type": "string",
                        "description": "The user goal, such as writing a post, improving a profile, or replying to a message.",
                    },
                },
                "required": ["page_type", "need"],
            },
        },
    }
]
