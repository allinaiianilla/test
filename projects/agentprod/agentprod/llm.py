"""LLM 适配层：统一封装 OpenAI Responses API。

要点：
- 消息格式在系统内部统一用 OpenAI Responses API 的 InputItem 风格：
  {"role": "user"|"assistant"|"system"|"developer", "content": str}
  {"type": "function_call", "call_id", "name", "arguments"}
  {"type": "function_call_output", "call_id", "output"}
- 工具 schema 用 Responses API 的 function 格式：
  {"type": "function", "name", "description", "parameters"}
- 输出统一解析为 AgentTurn（文本 + 工具调用列表）
- 支持 429/5xx 指数退避重试
- 不硬编码模型：从 ModelProfile 取连接参数，运行时可换
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Optional

from .config import ModelProfile
from .adapters import ProtocolAdapter

try:
    from openai import OpenAI
except ImportError as e:  # pragma: no cover
    raise ImportError("需要 openai>=1.x：pip install openai") from e


@dataclass
class ToolCall:
    """一次模型发起的工具调用。"""
    call_id: str
    name: str
    arguments: str            # JSON 字符串


@dataclass
class AgentTurn:
    """模型一轮输出的解析结果。"""
    text: Optional[str] = None
    tool_calls: list = field(default_factory=list)

    @property
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls)


class LLMClient:
    """对 Responses API 的薄封装。一个 profile 一个实例。"""

    def __init__(self, profile: ModelProfile, client=None):
        self.profile = profile
        self.adapter = ProtocolAdapter(profile.protocol)
        self._client = client or OpenAI(
            api_key=profile.api_key or "dummy-key",
            base_url=profile.base_url,
        )

    # ---------- 消息转换 ----------

    @staticmethod
    def _item_to_input(item: dict) -> dict:
        """内部消息 → Responses API input 项。

        内部格式即 Responses 风格，这里主要做防御性校验和规范化，
        并把 tool/system 角色映射为 API 要求的形式。
        """
        t = item.get("type")
        if t == "function_call":
            return {
                "type": "function_call",
                "call_id": item["call_id"],
                "name": item["name"],
                "arguments": item.get("arguments", "{}"),
            }
        if t == "function_call_output":
            return {
                "type": "function_call_output",
                "call_id": item["call_id"],
                "output": item.get("output", ""),
            }
        role = item.get("role", "user")
        content = item.get("content", "")
        if isinstance(content, (dict, list)):
            content = json.dumps(content, ensure_ascii=False)
        if role == "system":
            # Responses API 推荐用 developer 角色传行为指令
            return {"role": "developer", "content": str(content)}
        return {"role": role, "content": str(content)}

    @staticmethod
    def _to_wire(messages: list) -> list:
        """内部消息 → 可 JSON 序列化的 Responses 协议消息。

        system 角色映射为 developer（Responses API 推荐的行为指令角色）。
        """
        out = []
        for m in messages:
            if m.get("type") == "__assistant_turn__":
                turn: AgentTurn = m["turn"]
                if turn.text:
                    out.append({"role": "assistant", "content": turn.text})
                for c in turn.tool_calls:
                    out.append({"type": "function_call", "call_id": c.call_id,
                                "name": c.name,
                                "arguments": c.arguments or "{}"})
                continue
            item = dict(m)   # 拷贝，避免污染内部历史
            if item.get("role") == "system":
                item["role"] = "developer"
            out.append(item)
        return out

    @staticmethod
    def _tools_to_api(tools: list) -> list:
        """内部工具 schema → Responses API tools 格式。"""
        out = []
        for t in tools:
            out.append({
                "type": "function",
                "name": t["name"],
                "description": t.get("description", ""),
                "parameters": t.get("parameters", {"type": "object", "properties": {}}),
            })
        return out

    # ---------- 核心调用 ----------

    def complete(self, messages: list, tools: list = None,
                 max_output_tokens: int = None) -> AgentTurn:
        """跑一轮模型。内部统一 Responses 协议，出网关按 profile.protocol 适配。"""
        # 序列化前把 AgentTurn 块展开为协议消息
        wire_messages = self._to_wire(messages)
        params = self.adapter.build_request(
            wire_messages, tools, self.profile.model, self.profile.temperature,
            max_output_tokens or self.profile.max_output_tokens)

        if self.adapter.protocol == "responses":
            resp = self._request_with_retry(self._client.responses.create,
                                             params)
        else:
            resp = self._request_with_retry(self._client.chat.completions.create,
                                             params)
        return self.adapter.parse_response(resp)

    def _request_with_retry(self, fn, params: dict, max_retries: int = 4):
        """带指数退避的请求。429/5xx/超时重试。"""
        delay = 1.0
        last_err = None
        for attempt in range(max_retries + 1):
            try:
                return fn(**params)
            except Exception as e:  # noqa: BLE001
                last_err = e
                msg = str(e)
                retryable = ("429" in msg or "rate" in msg.lower()
                             or "timeout" in msg.lower() or "timed out" in msg.lower())
                status = getattr(getattr(e, "response", None), "status_code", None)
                if status is not None and (status == 429 or status >= 500):
                    retryable = True
                if not retryable or attempt == max_retries:
                    raise
                time.sleep(delay)
                delay *= 2
        raise last_err  # pragma: no cover


class LLMRouter:
    """模型档案路由器：支持运行时切换（这是"切换接口的方法"的落点）。

    - switch_model(name) 切换当前档案（新对话生效）
    - Agent 可通过 switch_model 工具委托切换
    - 摘要压缩用独立配置的 summary model
    """

    def __init__(self, profiles: dict, default: str, summary: str):
        self.profiles = profiles
        self.default_name = default
        self.summary_name = summary
        self._clients: dict = {}

    def get_client(self, profile_name: str = None) -> LLMClient:
        name = profile_name or self.default_name
        if name not in self.profiles:
            raise KeyError(f"未知模型档案: {name}")
        if name not in self._clients:
            self._clients[name] = LLMClient(self.profiles[name])
        return self._clients[name]

    @property
    def default_client(self) -> LLMClient:
        return self.get_client(self.default_name)

    @property
    def summary_client(self) -> LLMClient:
        return self.get_client(self.summary_name)

    def switch_model(self, new_default: str) -> str:
        """切换全局默认模型档案。"""
        if new_default not in self.profiles:
            raise KeyError(f"未知模型档案: {new_default}")
        old = self.default_name
        self.default_name = new_default
        return old
