"""协议适配层：Responses 协议 ↔ Chat Completions 协议 双向翻译。

背景：OpenAI Responses API 是新协议，但大量平台（智谱/DeepSeek/本地 vLLM
旧版/NVIDIA NIM）只支持 Chat Completions。适配器让框架内部永远只面对
Responses 协议，出网关时按平台自动翻译。

翻译规则：
- messages: developer→system，function_call/output ↔ tool_calls/tool 角色
- tools: 平铺格式 {type,name,description,parameters} ↔ 嵌套 {function:{...}}
- 响应: choices[0].message → AgentTurn（content + tool_calls）
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import List


@dataclass
class ToolCall:
    """一次模型发起的工具调用（与 llm.ToolCall 结构一致，避免循环导入）。"""
    call_id: str
    name: str
    arguments: str


@dataclass
class AgentTurn:
    """模型一轮输出的解析结果。"""
    text: object = None
    tool_calls: list = field(default_factory=list)

    @property
    def has_tool_calls(self) -> bool:
        return bool(self.tool_calls)


# ---------------- 请求方向：Responses → ChatCompletions ----------------

def merge_tool_call_blocks(messages: list) -> list:
    """把 __assistant_turn__ 块展开为合并的 assistant 轮次。

    Agent.messages 里的 assistant 轮次存为 {"type":"__assistant_turn__",
    "turn": AgentTurn}；CC 协议要求同一轮的多个 tool_calls 放在同一条
    assistant 消息里，且可带 content 文本。
    """
    out = []
    for m in messages:
        if m.get("type") == "__assistant_turn__":
            turn = m["turn"]
            calls = [{"call_id": c.call_id, "name": c.name,
                      "arguments": c.arguments} for c in turn.tool_calls]
            prev = out[-1] if out else None
            if prev is not None and prev.get("type") == "__merged_assistant__":
                # 防御性：相邻同类型块合并
                if turn.text:
                    prev["text"] = (prev.get("text") or "") + turn.text
                prev["calls"].extend(calls)
            else:
                out.append({"type": "__merged_assistant__",
                            "text": turn.text, "calls": calls})
        elif m.get("type") == "function_call":
            # wire 格式（LLMClient._to_wire 产物）：逐块收，相邻合并
            call = {"call_id": m["call_id"], "name": m["name"],
                    "arguments": m.get("arguments", "{}")}
            prev = out[-1] if out else None
            if prev is not None and prev.get("type") == "__merged_assistant__":
                prev["calls"].append(call)
            else:
                out.append({"type": "__merged_assistant__",
                            "text": None, "calls": [call]})
        else:
            out.append(m)
    return out


def responses_input_to_cc(messages: list) -> list:
    """内部消息序列 → chat/completions messages。"""
    out = []
    for m in messages:
        t = m.get("type")
        if t == "__merged_assistant__":
            entry = {"role": "assistant", "content": m.get("text") or None}
            if m.get("calls"):
                entry["tool_calls"] = [{
                    "id": c["call_id"], "type": "function",
                    "function": {"name": c["name"],
                                 "arguments": c.get("arguments", "{}")}}
                    for c in m["calls"]]
            out.append(entry)
        elif t == "function_call_output":
            out.append({"role": "tool", "tool_call_id": m["call_id"],
                        "content": str(m.get("output", ""))})
        else:
            role = m.get("role", "user")
            content = m.get("content", "")
            if isinstance(content, (dict, list)):
                content = json.dumps(content, ensure_ascii=False)
            if role == "developer":
                role = "system"
            out.append({"role": role, "content": str(content)})
    return out


def responses_tools_to_cc(tools: list) -> list:
    """平铺工具 schema → CC 嵌套格式。"""
    out = []
    for t in tools or []:
        out.append({"type": "function",
                    "function": {"name": t["name"],
                                 "description": t.get("description", ""),
                                 "parameters": t.get("parameters",
                                                     {"type": "object",
                                                      "properties": {}})}})
    return out


# ---------------- 响应方向：CC → AgentTurn ----------------

def cc_response_to_turn(resp: dict) -> AgentTurn:
    """chat/completions 响应 → AgentTurn。"""
    choice = resp["choices"][0]
    msg = choice.get("message", {})
    turn = AgentTurn(text=msg.get("content") or None)
    for tc in msg.get("tool_calls") or []:
        fn = tc.get("function", {})
        turn.tool_calls.append(ToolCall(
            call_id=tc.get("id", f"call_{len(turn.tool_calls)}"),
            name=fn.get("name", ""),
            arguments=fn.get("arguments") or "{}"))
    return turn


# ---------------- 协议探断 ----------------

class ProtocolAdapter:
    """按 profile 选择协议：responses 原生或 cc 适配。"""

    def __init__(self, protocol: str = "responses"):
        protocol = (protocol or "responses").lower()
        if protocol not in ("responses", "chat-completions"):
            raise ValueError(f"未知协议: {protocol}")
        self.protocol = protocol

    def build_request(self, messages: list, tools: list,
                      model: str, temperature: float,
                      max_output_tokens: int) -> dict:
        if self.protocol == "responses":
            params = {"model": model, "input": messages,
                      "max_output_tokens": max_output_tokens}
            if tools:
                params["tools"] = tools
            if temperature is not None:
                params["temperature"] = temperature
            return params
        # chat-completions
        merged = merge_tool_call_blocks(messages)
        params = {"model": model,
                  "messages": responses_input_to_cc(merged),
                  "max_tokens": max_output_tokens}
        if tools:
            params["tools"] = responses_tools_to_cc(tools)
            params["tool_choice"] = "auto"
        if temperature is not None:
            params["temperature"] = temperature
        return params

    def parse_response(self, resp_obj) -> AgentTurn:
        """从 SDK 响应对象解析（两种协议都兼容：鸭子类型判断）。"""
        # Responses API: resp.output 数组
        if hasattr(resp_obj, "output"):
            turn = AgentTurn()
            for block in resp_obj.output:
                btype = getattr(block, "type", None)
                if btype == "message":
                    parts = []
                    for c in block.content or []:
                        if getattr(c, "type", None) == "output_text":
                            parts.append(c.text)
                    if parts:
                        turn.text = (turn.text or "") + "".join(parts)
                elif btype == "function_call":
                    turn.tool_calls.append(ToolCall(
                        call_id=block.call_id, name=block.name,
                        arguments=block.arguments or "{}"))
            return turn
        # Chat Completions: resp.choices[0].message
        if hasattr(resp_obj, "choices"):
            return cc_response_to_turn(
                {"choices": [{"message": {
                    "content": resp_obj.choices[0].message.content,
                    "tool_calls": [
                        {"id": tc.id, "function": {"name": tc.function.name,
                                                   "arguments": tc.function.arguments}}
                        for tc in (resp_obj.choices[0].message.tool_calls or [])],
                }}]})
        raise ValueError("无法识别的响应格式")
