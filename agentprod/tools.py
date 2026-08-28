"""工具系统：注册、schema 生成、批执行（并行 + 分组挂起 + 审批）。

落地讨论过的关键设计：
1. 工具 = 普通函数 + ToolSpec 元数据（dangerous 标记触发审批）
2. ask_human 单独识别：批内其他工具先跑完并落袋，ask_human 触发 PauseForHuman
3. 批内并行（asyncio.gather），失败也要产出 result（错误信息本身是结果）
4. 每个工具执行有超时保护
"""
from __future__ import annotations

import asyncio
import inspect
import json
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Optional


class PauseForHuman(Exception):
    """挂起信号：不是错误，是控制流——跨层跳出到交互层。

    携带问题文本与 call_id；已完成的同批结果此时已安全写入 messages。
    """

    def __init__(self, call_id: str, question: str, meta: Optional[dict] = None):
        self.call_id = call_id
        self.question = question
        self.meta = meta or {}
        super().__init__(question)


@dataclass
class ToolSpec:
    name: str
    description: str
    parameters: dict                    # JSON schema
    func: Callable                      # 同步或异步函数
    dangerous: bool = False             # True → 执行前需人工审批
    timeout: float = 60.0
    is_ask_human: bool = False
    is_switch_model: bool = False
    group: str = "general"

    def to_schema(self) -> dict:
        """给 Responses API 的 schema（平铺格式）。"""
        return {
            "type": "function",
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters,
        }


class ToolRegistry:
    """工具注册表：名字 → ToolSpec。"""

    def __init__(self):
        self._tools: dict = {}

    def register(self, spec: ToolSpec):
        if spec.name in self._tools:
            raise ValueError(f"工具重复注册: {spec.name}")
        self._tools[spec.name] = spec

    def register_function(self, name: str, description: str, parameters: dict,
                          func: Callable, **kw):
        self.register(ToolSpec(name=name, description=description,
                               parameters=parameters, func=func, **kw))

    def get(self, name: str) -> Optional[ToolSpec]:
        return self._tools.get(name)

    def schemas(self, names: list = None) -> list:
        if names is None:
            return [t.to_schema() for t in self._tools.values()]
        return [self._tools[n].to_schema() for n in names if n in self._tools]

    def __contains__(self, name: str) -> bool:
        return name in self._tools

    def names(self) -> list:
        return list(self._tools)


def make_result(call_id: str, ok: bool, data: Any = None,
                error: str = None, truncate_note: str = None) -> dict:
    """统一工具结果信封。所有工具输出走这个格式，便于模型理解。"""
    payload = {"ok": ok}
    if data is not None:
        payload["data"] = data
    if error:
        payload["error"] = error
    if truncate_note:
        payload["note"] = truncate_note
    return {"call_id": call_id, "result": payload}


def clamp_text(text: str, max_chars: int = 24000) -> tuple:
    """长结果截断：返回 (文本, 截断说明或 None)。配合落盘外置使用。"""
    if len(text) <= max_chars:
        return text, None
    note = (f"结果过大已截断（{len(text)} 字符 → 保留前 {max_chars}）。"
            f"建议改用聚合查询或 save_to_file 参数落盘。")
    return text[:max_chars], note


class ToolExecutor:
    """批执行器：审批回调 + ask_human 挂起 + 并行执行。"""

    def __init__(self, registry: ToolRegistry,
                 approver: Callable = None,
                 progress: Callable = None,
                 ask_handler: Callable = None):
        """
        approver:  async (ToolSpec, args) -> bool   危险工具审批
        progress:  async (ToolSpec, args) -> None   进度播报
        ask_handler: async (call_id, question, meta) -> None
                     ask_human 的实际问人实现（由聊天层注入）
        """
        self.registry = registry
        self.approver = approver
        self.progress = progress
        self.ask_handler = ask_handler

    async def execute_batch(self, tool_calls: list,
                            max_results_per_batch: int = None) -> list:
        """执行一批工具调用。

        返回 messages 可直接使用的 function_call_output 列表（不含 ask_human
        挂起的那一个——那种情况下抛 PauseForHuman，由 Agent 层处理）。

        规则：
        - 普通（非问人）工具先并行执行，结果立即返回
        - 若含 ask_human：抛 PauseForHuman；同批普通结果已在返回前生成
          （调用方应先落袋这些结果再处理挂起）
        - 危险工具先过审批；拒绝时产出 ok=False 结果而非中断
        """
        normal, asks = [], []
        for c in tool_calls:
            spec = self.registry.get(c.name)
            if spec and spec.is_ask_human:
                asks.append((c, spec))
            else:
                normal.append((c, spec))

        # ---- 1. 普通工具并行执行 ----
        results = []
        if normal:
            coros = [self._run_one(c, spec) for c, spec in normal]
            outs = await asyncio.gather(*coros)
            results.extend(outs)

        # ---- 2. ask_human：先落袋普通结果，再挂起 ----
        if asks:
            call, _spec = asks[0]
            question, meta = self._parse_ask(call)
            if len(asks) > 1:
                meta["queued_asks"] = [
                    {"call_id": c.call_id,
                     "arguments": json.loads(c.arguments or "{}")}
                    for c, _ in asks[1:]]
            # 先把普通结果交还调用方落袋，再抛挂起
            raise _PendingWithResults(results, call.call_id, question, meta)

        return results

    def _parse_ask(self, call):
        try:
            args = json.loads(call.arguments or "{}")
        except json.JSONDecodeError:
            args = {}
        question = str(args.get("question", "请补充信息："))
        meta = {"raw_args": args}
        return question, meta

    async def _run_one(self, call, spec: Optional[ToolSpec]) -> dict:
        """执行单个工具调用，任何异常都转化为结果信封。"""
        if spec is None:
            return make_result(call.call_id, ok=False,
                               error=f"未知工具: {call.name}")

        try:
            args = json.loads(call.arguments or "{}") if call.arguments else {}
        except json.JSONDecodeError as e:
            return make_result(call.call_id, ok=False,
                               error=f"参数 JSON 解析失败: {e}")

        # 进度播报（不阻塞，失败忽略）
        if self.progress:
            try:
                await self._maybe_await(self.progress, spec, args)
            except Exception:  # noqa: BLE001
                pass

        # 危险工具审批
        if spec.dangerous:
            if self.approver is None:
                return make_result(call.call_id, ok=False,
                                   error="危险工具无审批通道，已拒绝执行")
            try:
                approved = await self._maybe_await(self.approver, spec, args)
            except Exception as e:  # noqa: BLE001
                approved = False
                args_desc = str(e)
            if not approved:
                return make_result(call.call_id, ok=False,
                                   error="用户拒绝了本次操作",
                                   data={"tool": spec.name, "args": args})

        # 执行（带超时）
        try:
            raw = await asyncio.wait_for(
                self._invoke(spec.func, args), timeout=spec.timeout)
        except asyncio.TimeoutError:
            return make_result(call.call_id, ok=False,
                               error=f"工具执行超时（>{spec.timeout}s）")
        except Exception as e:  # noqa: BLE001
            tb = traceback.format_exc(limit=3)
            return make_result(call.call_id, ok=False,
                               error=f"工具执行失败: {e}", data={"traceback": tb})

        # 输出规整：对象 → JSON 字符串
        if isinstance(raw, (dict, list)):
            raw = json.dumps(raw, ensure_ascii=False)
        raw = "" if raw is None else str(raw)
        text, note = clamp_text(raw)
        return make_result(call.call_id, ok=True, data=text,
                           truncate_note=note)

    @staticmethod
    async def _invoke(func: Callable, args: dict):
        if inspect.iscoroutinefunction(func):
            return await func(**args)
        return func(**args)

    @staticmethod
    async def _maybe_await(fn, *a, **kw):
        if inspect.iscoroutinefunction(fn):
            return await fn(*a, **kw)
        return fn(*a, **kw)


class _PendingWithResults(Exception):
    """内部信号：ask_human 挂起 + 携带同批已完成结果。"""

    def __init__(self, results: list, call_id: str,
                 question: str, meta: dict):
        self.results = results
        self.call_id = call_id
        self.question = question
        self.meta = meta
        super().__init__(question)
