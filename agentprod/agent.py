"""Agent 核心：主循环 + 上下文压缩 + 子 Agent spawn。

落地讨论过的设计：
- 配置驱动（AgentConfig），复用 = 换配置
- run() 循环：调模型 → 并行执行工具批 → 结果回填 → 直到无工具调用或步数超限
- ask_human 批内分组：普通工具结果先落袋，再抛 PauseForHuman
- resume()：用户回复包装成 function_call_output，从断点续跑
- 上下文压缩：估算 token 超 compaction_ratio 阈值 → 旧史摘要化
  （切分边界保证 function_call 与其输出不被拆散）
- spawn：工厂注入（无循环依赖）+ 深度限制，子 agent 非交互
"""
from __future__ import annotations

import asyncio
import json
import time
from dataclasses import dataclass, field
from typing import Callable, Optional

from .config import AgentConfig
from .llm import AgentTurn, LLMRouter, ToolCall
from .tools import (PauseForHuman, ToolExecutor, ToolRegistry,
                    _PendingWithResults, make_result)


def estimate_tokens(messages: list) -> int:
    """粗估 token（中文约 1 字/token，英文约 4 字符/token，折中取 2.5）。"""
    total = 0
    for m in messages:
        c = m.get("content") or m.get("output") or ""
        if isinstance(c, (dict, list)):
            c = json.dumps(c, ensure_ascii=False)
        total += len(str(c))
        # 工具调用块的参数也算
        if m.get("type") == "__assistant_turn__":
            for c2 in m["turn"].tool_calls:
                total += len(c2.arguments) + len(c2.name)
    return int(total / 2.5)


@dataclass
class PendingAsk:
    """挂起状态：等待用户回答某个 function_call。"""
    call_id: str
    question: str
    meta: dict = field(default_factory=dict)
    created_at: float = field(default_factory=time.time)
    queued_asks: list = field(default_factory=list)   # 同批后续待问问题


class Agent:
    """一个运行时 Agent 实例。一个会话一个实例，状态在实例里。"""

    def __init__(self, config: AgentConfig, router: LLMRouter,
                 tool_registry: ToolRegistry,
                 depth: int = 0, model_profile: str = None,
                 executor_kwargs: Optional[dict] = None,
                 session_store=None,
                 spawn_factory: Callable = None):
        self.cfg = config
        self.router = router
        self.registry = tool_registry
        self.depth = depth
        self.model_profile = model_profile or config.model or router.default_name
        self.messages: list = [
            {"role": "system", "content": config.system_prompt}]
        self.pending: Optional[PendingAsk] = None
        self.steps_used = 0
        self.finished_text: Optional[str] = None
        self._executor_kwargs = executor_kwargs or {}
        self._session_store = session_store
        self._spawn_factory = spawn_factory

    # ------------------------------------------------------------------ #
    # 主循环
    # ------------------------------------------------------------------ #

    async def run(self, user_text: str) -> str:
        """处理一条用户消息；需要问用户时抛 PauseForHuman。"""
        self._append_user(user_text)
        try:
            return await self._loop()
        finally:
            self._persist()

    async def resume(self, answer: str) -> str:
        """用户回答挂起的问题后，从断点继续。"""
        if not self.pending:
            return await self.run(answer)  # 无挂起 → 当新消息处理
        p = self.pending
        self.messages.append({
            "type": "function_call_output",
            "call_id": p.call_id,
            "output": json.dumps(
                {"ok": True, "data": f"用户回复：{answer}"}, ensure_ascii=False),
        })
        # 同批还有排队的问题 → 继续问下一个（串行问完）
        if p.queued_asks:
            nxt = p.queued_asks[0]
            self.pending = PendingAsk(
                call_id=nxt["call_id"],
                question=str(nxt.get("arguments", {}).get("question",
                                                          "请补充信息：")),
                queued_asks=p.queued_asks[1:],
            )
            self._persist()
            raise PauseForHuman(self.pending.call_id, self.pending.question)
        self.pending = None
        try:
            return await self._loop()
        finally:
            self._persist()

    async def _loop(self) -> str:
        executor = self._make_executor()
        # schema 与执行共用"绑定后的注册表"：
        # 无权限的工具对模型也不可见（最小暴露面）
        tools = executor.registry.schemas(self.cfg.tool_names)
        while self.steps_used < self.cfg.max_steps:
            self.steps_used += 1
            client = self.router.get_client(self.model_profile)
            turn = await asyncio.to_thread(
                client.complete, self.messages, tools or None)

            # 记录 assistant 消息（含工具调用）
            if turn.has_tool_calls:
                self.messages.append({"type": "__assistant_turn__",
                                      "turn": turn})
            elif turn.text is not None:
                self.messages.append({"role": "assistant", "content": turn.text})
                self.finished_text = turn.text

            if not turn.has_tool_calls:
                return turn.text or ""

            # ---- 执行工具批（并行 + 分组挂起） ----
            try:
                outputs = await executor.execute_batch(turn.tool_calls)
            except _PendingWithResults as pr:      # ask_human 挂起
                for r in pr.results:
                    self._append_output(r)
                self.pending = PendingAsk(
                    call_id=pr.call_id, question=pr.question,
                    meta=pr.meta,
                    queued_asks=pr.meta.get("queued_asks", []))
                self._persist()
                raise PauseForHuman(pr.call_id, pr.question, pr.meta)
            for r in outputs:
                self._append_output(r)

            # 每轮检查压缩
            self._compact_if_needed()
        return self.finished_text or "已达最大步数限制，任务未完成。"

    # ------------------------------------------------------------------ #
    # 上下文压缩
    # ------------------------------------------------------------------ #

    def _compact_if_needed(self):
        profile = self.router.profiles[self.model_profile]
        threshold = profile.context_window * profile.compaction_ratio
        if estimate_tokens(self.messages) < threshold:
            return

        keep = 8
        head = self.messages[:1]
        body = self.messages[1:]
        if len(body) <= keep:
            return
        old, recent = body[:-keep], body[-keep:]

        # 边界守卫：function_call_output 不能与它的 assistant 调用块分离
        while recent and recent[0].get("type") == "function_call_output":
            old.append(recent.pop(0))

        summary = self._summarize(old)
        self.messages = head + [
            {"role": "system",
             "content": f"[历史摘要] 之前对话的压缩总结：\n{summary}"},
        ] + recent

    def _summarize(self, old_messages: list) -> str:
        client = self.router.summary_client
        dump = "\n".join(self._render_message(m) for m in old_messages)
        prompt = (
            "把以下 Agent 对话历史压缩成要点摘要，必须保留：\n"
            "1) 任务目标与用户核心诉求 2) 已完成的步骤与关键结论 "
            "3) 关键数据/数字/文件路径 4) 未完成事项与下一步计划。\n"
            "省略过程性细节。输出 300 字以内。\n\n" + dump)
        try:
            turn = client.complete([{"role": "user", "content": prompt}])
            return turn.text or "(摘要生成失败，已丢弃旧历史)"
        except Exception:  # noqa: BLE001
            return "(摘要生成失败，已丢弃旧历史)"

    # ------------------------------------------------------------------ #
    # 子 Agent（工厂注入，无循环依赖）
    # ------------------------------------------------------------------ #

    async def spawn(self, agent_name: str, task: str) -> str:
        """派生子 agent 干活，只回收结论。"""
        if not self.cfg.can_spawn:
            return json.dumps({"ok": False, "error": "该角色无权 spawn 子 agent"})
        if self.depth >= self.cfg.spawn_depth_max:
            return json.dumps({"ok": False,
                               "error": f"已达最大递归深度 {self.cfg.spawn_depth_max}"})
        if self._spawn_factory is None:
            return json.dumps({"ok": False, "error": "未配置 spawn 工厂"})
        try:
            child = self._spawn_factory(agent_name, depth=self.depth + 1)
        except KeyError:
            return json.dumps({"ok": False, "error": f"未知 agent 角色: {agent_name}"})
        # 子 agent 非交互：不能问用户（防深度弹窗打扰）
        child.cfg.interactive = False
        try:
            result = await child.run(task)
            return json.dumps({"ok": True, "data": result}, ensure_ascii=False)
        except PauseForHuman:
            return json.dumps({"ok": False,
                               "error": "子任务需要用户补充信息，已取消（子 agent 不可交互）"})

    # ------------------------------------------------------------------ #
    # 模型切换（会话级）
    # ------------------------------------------------------------------ #

    def switch_model(self, profile_name: str) -> str:
        if profile_name not in self.router.profiles:
            avail = ", ".join(self.router.profiles)
            return json.dumps({"ok": False,
                               "error": f"未知模型档案。可用：{avail}"})
        old = self.model_profile
        self.model_profile = profile_name
        self._persist()
        return json.dumps({"ok": True, "data": {
            "from": old, "to": profile_name,
            "model": self.router.profiles[profile_name].model}},
            ensure_ascii=False)

    # ------------------------------------------------------------------ #
    # 内部
    # ------------------------------------------------------------------ #

    def _make_executor(self) -> ToolExecutor:
        """默认执行器（未绑定会话工具）。binding.py 会打补丁增强。"""
        kw = dict(self._executor_kwargs)
        return ToolExecutor(self.registry,
                            approver=kw.get("approver"),
                            progress=kw.get("progress"),
                            ask_handler=None)

    def _append_user(self, text: str):
        self.messages.append({"role": "user", "content": text})

    def _append_output(self, r: dict):
        self.messages.append({
            "type": "function_call_output",
            "call_id": r["call_id"],
            "output": json.dumps(r["result"], ensure_ascii=False),
        })

    def _persist(self):
        if self._session_store is not None:
            try:
                self._session_store.save_agent_state(self)
            except Exception:  # noqa: BLE001
                pass

    @staticmethod
    def _render_message(m: dict) -> str:
        t = m.get("type")
        if t == "__assistant_turn__":
            turn: AgentTurn = m["turn"]
            parts = [f"assistant: {turn.text or ''}"]
            for c in turn.tool_calls:
                parts.append(f"  → 调用工具 {c.name}({c.arguments})")
            return "\n".join(parts)
        if t == "function_call_output":
            return f"tool_result[{m['call_id']}]: {str(m['output'])[:200]}"
        role = m.get("role", "?")
        return f"{role}: {str(m.get('content', ''))[:300]}"

    # ------------------------------------------------------------------ #
    # 序列化（会话持久化用）
    # ------------------------------------------------------------------ #

    def to_state(self) -> dict:
        msgs = []
        for m in self.messages:
            if m.get("type") == "__assistant_turn__":
                turn: AgentTurn = m["turn"]
                msgs.append({
                    "type": "function_call_block",
                    "text": turn.text,
                    "calls": [{"call_id": c.call_id, "name": c.name,
                               "arguments": c.arguments}
                              for c in turn.tool_calls]})
            else:
                msgs.append(m)
        return {
            "agent_role": self.cfg.name,
            "model_profile": self.model_profile,
            "depth": self.depth,
            "steps_used": self.steps_used,
            "messages": msgs,
            "pending": (None if not self.pending else {
                "call_id": self.pending.call_id,
                "question": self.pending.question,
                "meta": self.pending.meta,
                "queued_asks": self.pending.queued_asks,
            }),
            "finished_text": self.finished_text,
        }

    @classmethod
    def from_state(cls, state: dict, router: LLMRouter,
                   tool_registry: ToolRegistry,
                   agent_configs: dict, session_store=None,
                   spawn_factory: Callable = None):
        cfg = agent_configs[state["agent_role"]]
        agent = cls(cfg, router, tool_registry,
                    depth=state.get("depth", 0),
                    model_profile=state.get("model_profile"),
                    session_store=session_store,
                    spawn_factory=spawn_factory)
        agent.messages = []
        for m in state.get("messages", []):
            if m.get("type") == "function_call_block":
                turn = AgentTurn(text=m.get("text"))
                turn.tool_calls = [ToolCall(**c) for c in m.get("calls", [])]
                agent.messages.append({"type": "__assistant_turn__",
                                       "turn": turn})
            else:
                agent.messages.append(m)
        if not agent.messages or agent.messages[0].get("role") != "system":
            agent.messages.insert(0, {"role": "system",
                                      "content": cfg.system_prompt})
        if state.get("pending"):
            agent.pending = PendingAsk(**state["pending"])
        agent.steps_used = state.get("steps_used", 0)
        agent.finished_text = state.get("finished_text")
        return agent
