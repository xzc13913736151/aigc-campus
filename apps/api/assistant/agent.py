from __future__ import annotations

from dataclasses import dataclass
import json
import os
from pathlib import Path
import re
from typing import Any

import requests
from django.conf import settings


@dataclass(frozen=True)
class AgentConfig:
    api_key: str = ""
    base_url: str = ""
    model: str = ""
    endpoint_path: str = "/chat/completions"
    timeout_seconds: int = 30
    temperature: float = 0.7
    max_tokens: int = 800

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.base_url and self.model)


class AgentCallError(RuntimeError):
    pass


def _parse_scalar(value: str) -> Any:
    value = value.strip().strip('"').strip("'")
    if value.lower() in {"true", "false"}:
        return value.lower() == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


def _load_simple_yaml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}

    data: dict[str, Any] = {}
    current_section: str | None = None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.split("#", 1)[0].rstrip()
        if not line.strip():
            continue

        if not line.startswith(" ") and line.endswith(":"):
            current_section = line[:-1].strip()
            data.setdefault(current_section, {})
            continue

        if ":" not in line:
            continue

        key, value = line.split(":", 1)
        key = key.strip()
        parsed_value = _parse_scalar(value)
        if current_section and line.startswith(" "):
            section = data.setdefault(current_section, {})
            if isinstance(section, dict):
                section[key] = parsed_value
            continue
        data[key] = parsed_value
    return data


def load_agent_config() -> AgentConfig:
    config_path = Path(os.getenv("AGENT_CONFIG_PATH", settings.REPO_DIR / "config.yaml"))
    raw_config = _load_simple_yaml(config_path)
    agent_config = raw_config.get("agent", {})
    if not isinstance(agent_config, dict):
        agent_config = {}

    return AgentConfig(
        api_key=os.getenv("AGENT_API_KEY", str(agent_config.get("api_key", ""))).strip(),
        base_url=os.getenv("AGENT_BASE_URL", str(agent_config.get("base_url", ""))).strip().rstrip("/"),
        model=os.getenv("AGENT_MODEL", str(agent_config.get("model", ""))).strip(),
        endpoint_path=os.getenv("AGENT_ENDPOINT_PATH", str(agent_config.get("endpoint_path", "/chat/completions"))).strip() or "/chat/completions",
        timeout_seconds=int(os.getenv("AGENT_TIMEOUT_SECONDS", agent_config.get("timeout_seconds", 30))),
        temperature=float(os.getenv("AGENT_TEMPERATURE", agent_config.get("temperature", 0.7))),
        max_tokens=int(os.getenv("AGENT_MAX_TOKENS", agent_config.get("max_tokens", 800))),
    )


def _completion_url(config: AgentConfig) -> str:
    if config.base_url.rstrip("/").endswith(config.endpoint_path.strip("/")):
        return config.base_url
    endpoint = config.endpoint_path if config.endpoint_path.startswith("/") else f"/{config.endpoint_path}"
    return f"{config.base_url}{endpoint}"


def _run_local_tool(name: str, arguments: dict[str, Any]) -> str:
    if name != "campusclaw_context":
        return "没有找到对应的工具。"

    page_type = str(arguments.get("page_type", "general"))
    need = str(arguments.get("need", ""))
    page_guides = {
        "forum": "论坛页默认展示最新帖子，适合校园日常、求助、经验分享、活动信息和话题讨论。",
        "publish": "发布页支持发帖子、发组队招募和公开恋爱匹配资料。",
        "messages": "消息页用于聊天沟通，建议回复自然、有边界、能推动下一步。",
        "me": "我的页面展示基础资料、头像昵称、黑名单和个人信息管理入口。",
        "general": "CampusClaw 聚焦校园论坛、组队匹配、恋爱匹配、消息聊天和 AI 建议。",
    }
    return f"{page_guides.get(page_type, page_guides['general'])} 当前用户需求：{need}"


def _post_completion(config: AgentConfig, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        response = requests.post(
            _completion_url(config),
            headers={
                "Authorization": f"Bearer {config.api_key}",
                "Content-Type": "application/json",
            },
            data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            timeout=config.timeout_seconds,
        )
        response.raise_for_status()
        return response.json()
    except requests.RequestException as exc:
        raise AgentCallError(f"Agent request failed: {exc}") from exc
    except ValueError as exc:
        raise AgentCallError("Agent response is not valid JSON.") from exc


def _extract_message(data: dict[str, Any]) -> dict[str, Any]:
    try:
        message = data["choices"][0]["message"]
    except (KeyError, IndexError, TypeError) as exc:
        raise AgentCallError("Agent response format is invalid.") from exc
    if not isinstance(message, dict):
        raise AgentCallError("Agent response message is invalid.")
    return message


def call_agent(messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> str:
    config = load_agent_config()
    if not config.enabled:
        raise AgentCallError("Agent config is incomplete.")

    payload: dict[str, Any] = {
        "model": config.model,
        "messages": messages,
        "temperature": config.temperature,
        "max_tokens": config.max_tokens,
    }
    if tools:
        payload["tools"] = tools
        payload["tool_choice"] = "auto"

    data = _post_completion(config, payload)
    message = _extract_message(data)
    tool_calls = message.get("tool_calls") or []
    if tool_calls:
        tool_messages = [*messages, message]
        for tool_call in tool_calls:
            function = tool_call.get("function", {}) if isinstance(tool_call, dict) else {}
            name = function.get("name", "")
            raw_arguments = function.get("arguments", "{}")
            try:
                arguments = json.loads(raw_arguments) if isinstance(raw_arguments, str) else raw_arguments
            except ValueError:
                arguments = {}
            tool_messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.get("id", ""),
                    "name": name,
                    "content": _run_local_tool(name, arguments if isinstance(arguments, dict) else {}),
                }
            )

        follow_up_payload = {
            "model": config.model,
            "messages": tool_messages,
            "temperature": config.temperature,
            "max_tokens": config.max_tokens,
        }
        data = _post_completion(config, follow_up_payload)
        message = _extract_message(data)

    content = str(message.get("content", "")).strip()
    if not content:
        raise AgentCallError("Agent returned an empty response.")
    return content


def _strip_json_fence(content: str) -> str:
    clean = content.strip()
    if not clean.startswith("```"):
        return clean
    clean = re.sub(r"^```(?:json)?\s*", "", clean, flags=re.IGNORECASE)
    clean = re.sub(r"\s*```$", "", clean)
    return clean.strip()


def call_agent_json(messages: list[dict[str, Any]], schema_name: str = "agent_json") -> dict[str, Any]:
    content = _strip_json_fence(call_agent(messages))
    try:
        data = json.loads(content)
    except ValueError as exc:
        raise AgentCallError(f"{schema_name} response is not valid JSON.") from exc
    if not isinstance(data, dict):
        raise AgentCallError(f"{schema_name} response must be a JSON object.")
    return data
