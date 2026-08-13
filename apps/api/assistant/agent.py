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
    user_id: str = "campusclaw"
    timeout_seconds: int = 30

    @property
    def enabled(self) -> bool:
        return bool(self.api_key and self.base_url and self.user_id)


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
    agent_config = raw_config.get("hiagent", {})
    if not isinstance(agent_config, dict):
        agent_config = {}

    return AgentConfig(
        api_key=os.getenv("HIAGENT_API_KEY", str(agent_config.get("api_key", ""))).strip(),
        base_url=os.getenv("HIAGENT_BASE_URL", str(agent_config.get("base_url", ""))).strip().rstrip("/"),
        user_id=os.getenv("HIAGENT_USER_ID", str(agent_config.get("user_id", "campusclaw"))).strip(),
        timeout_seconds=int(os.getenv("HIAGENT_TIMEOUT_SECONDS", agent_config.get("timeout_seconds", 30))),
    )


def _endpoint_url(config: AgentConfig, endpoint: str) -> str:
    return f"{config.base_url}/{endpoint.lstrip('/')}"


def _headers(config: AgentConfig) -> dict[str, str]:
    return {
        "Apikey": config.api_key,
        "Content-Type": "application/json",
    }


def _format_query(messages: list[dict[str, Any]]) -> str:
    """Turn the existing prompt/history representation into HiAgent's Query field."""
    role_labels = {"system": "System", "user": "User", "assistant": "Assistant", "tool": "Tool"}
    rows: list[str] = []
    for message in messages:
        if not isinstance(message, dict):
            continue
        content = str(message.get("content", "")).strip()
        if content:
            rows.append(f"[{role_labels.get(str(message.get('role', 'user')), 'User')}]\n{content}")
    query = "\n\n".join(rows).strip()
    if not query:
        raise AgentCallError("Agent query is empty.")
    return query


def _compact_query(query: str, max_chars: int = 4800) -> str:
    """Keep HiAgent prompts below small agent context limits."""
    if len(query) <= max_chars:
        return query

    # Decision prompts put the verbose policy/examples before the live context.
    # Keep a short role instruction and the tail containing current state + user input.
    tail = query[-(max_chars - 900) :]
    return (
        query[:900]
        + "\n\n[Prompt shortened to fit HiAgent context limits.]\n"
        + "Return a single JSON object with keys: intent, user_signal, flow, payload_patch, "
        + "missing_fields, assistant_reply, should_create_actions, action_intents.\n"
        + tail
    )


def _post_json(config: AgentConfig, endpoint: str, payload: dict[str, Any]) -> dict[str, Any]:
    try:
        response = requests.post(
            _endpoint_url(config, endpoint),
            headers=_headers(config),
            json=payload,
            timeout=config.timeout_seconds,
        )
        response.raise_for_status()
        data = response.json()
    except requests.RequestException as exc:
        raise AgentCallError(f"HiAgent request failed: {exc}") from exc
    except ValueError as exc:
        raise AgentCallError("HiAgent response is not valid JSON.") from exc
    if not isinstance(data, dict):
        raise AgentCallError("HiAgent response format is invalid.")
    return data


def _create_conversation(config: AgentConfig) -> str:
    data = _post_json(config, "/create_conversation", {"UserID": config.user_id})
    try:
        conversation_id = str(data["Conversation"]["AppConversationID"]).strip()
    except (KeyError, TypeError) as exc:
        raise AgentCallError("HiAgent conversation response format is invalid.") from exc
    if not conversation_id:
        raise AgentCallError("HiAgent returned an empty conversation ID.")
    return conversation_id


def _query_conversation(config: AgentConfig, conversation_id: str, query: str) -> str:
    data = _post_json(
        config,
        "/chat_query_v2",
        {
            "UserID": config.user_id,
            "AppConversationID": conversation_id,
            "Query": query,
            "ResponseMode": "blocking",
        },
    )
    answer = _strip_provider_footer(str(data.get("answer", "")))
    if not answer:
        raise AgentCallError("HiAgent returned an empty answer.")
    return answer


def _strip_provider_footer(answer: str) -> str:
    """Remove HiAgent/Feishu attribution appended outside the model response."""
    return re.sub(r"\s*(?:本回答由\s*AI\s*生成|飞书端反馈|飛書端反饋).*?$", "", answer, flags=re.IGNORECASE | re.DOTALL).strip()


def call_agent(messages: list[dict[str, Any]], tools: list[dict[str, Any]] | None = None) -> str:
    """Call HiAgent in blocking mode. Tool definitions are unsupported by this API."""
    del tools
    config = load_agent_config()
    if not config.enabled:
        raise AgentCallError("HiAgent config is incomplete.")
    if not 1 <= len(config.user_id) <= 20:
        raise AgentCallError("HIAGENT_USER_ID must be between 1 and 20 characters.")

    query = _compact_query(_format_query(messages))
    conversation_id = _create_conversation(config)
    return _query_conversation(config, conversation_id, query)


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
