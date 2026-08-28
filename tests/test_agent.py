"""单元测试：不依赖真实 API key（用 FakeLLM 模拟 Responses API 行为）。

覆盖：
- 工具批执行：并行、失败留痕、截断
- ask_human 分组挂起：普通结果先落袋、排队问题
- Agent 循环：多轮工具调用 → 最终文本
- pending/resume：同一聊天口的路由
- 上下文压缩：阈值触发、保留 system 与最近轮
- 序列化/恢复：崩溃重启后续跑
- 只读 SQL 防护与强制 LIMIT
- 配置加载与模型切换
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from agentprod.config import (DATA_DIR, AgentConfig, ModelProfile)
from agentprod.llm import AgentTurn, LLMRouter, ToolCall
from agentprod.tools import (PauseForHuman, ToolExecutor, ToolRegistry,
                             ToolSpec, make_result)
from agentprod import builtin_tools, demo_db


# --------------------------------------------------------------------- #
# 测试基础设施
# --------------------------------------------------------------------- #

class FakeResponses:
    """按脚本回放 AgentTurn，并记录每次请求的 input。"""

    def __init__(self, script: list):
        self.script = list(script)   # 每项: AgentTurn
        self.i = 0
        self.calls = []              # 记录每次请求的 input

    def next_turn(self):
        turn = self.script[min(self.i, len(self.script) - 1)]
        self.i += 1
        return turn


class FakeLLMClient:
    """直接返回 AgentTurn（跳过网络与响应解析）。"""

    def __init__(self, script: list):
        self.responses = FakeResponses(script)

    def complete(self, messages, tools=None, max_output_tokens=None):
        self.responses.calls.append({"input": messages, "tools": tools})
        return self.responses.next_turn()


class _ClientWrap:
    """保持与 LLMClient 相同的同步 complete 接口。"""
    def __init__(self, client):
        self._c = client

    def complete(self, messages, tools=None, max_output_tokens=None):
        return self._c.complete(messages, tools=tools,
                                max_output_tokens=max_output_tokens)


def make_router(script: list, profiles=None):
    profiles = profiles or {
        "p1": ModelProfile(name="p1", model="fake-1", context_window=128000),
        "p2": ModelProfile(name="p2", model="fake-2", context_window=128000,
                           is_summary_model=True),
    }
    router = LLMRouter(profiles, "p1", "p2")
    router._clients["p1"] = _ClientWrap(FakeLLMClient(script))
    router._clients["p2"] = _ClientWrap(FakeLLMClient(
        [AgentTurn(text="摘要：用户要查销售数据，已完成查询，结论是A。")]))
    return router


def build_registry(spawn_impl=None, switch_impl=None,
                   list_models_impl=lambda: "{}"):
    reg = ToolRegistry()
    builtin_tools.register_builtin_tools(
        reg, spawn_impl=spawn_impl, switch_impl=switch_impl,
        list_models_impl=list_models_impl)
    return reg


def make_agent(script, cfg=None, registry=None, router=None):
    from agentprod.agent import Agent
    cfg = cfg or AgentConfig(
        name="main", system_prompt="test",
        tool_names=["get_time", "calculator", "ask_human"])
    router = router or make_router(script)
    registry = registry or build_registry()
    return Agent(cfg, router, registry)


# --------------------------------------------------------------------- #
# 1. 工具执行器
# --------------------------------------------------------------------- #

def test_batch_parallel_and_failure_trace():
    reg = ToolRegistry()
    reg.register_function("fast", "快工具", {"type": "object", "properties": {}},
                          lambda: "ok")
    reg.register_function("boom", "会炸的工具",
                          {"type": "object", "properties": {}},
                          lambda: 1 / 0)
    ex = ToolExecutor(reg)
    calls = [ToolCall(call_id="c1", name="fast", arguments="{}"),
             ToolCall(call_id="c2", name="boom", arguments="{}")]
    outs = asyncio.run(ex.execute_batch(calls))
    d = {o["call_id"]: o["result"] for o in outs}
    assert d["c1"]["ok"] is True
    assert d["c2"]["ok"] is False
    assert "失败" in d["c2"]["error"] or "错误" in d["c2"]["error"]


def test_unknown_tool_leaves_trace():
    reg = ToolRegistry()
    ex = ToolExecutor(reg)
    outs = asyncio.run(ex.execute_batch(
        [ToolCall(call_id="x", name="nope", arguments="{}")]))
    assert outs[0]["result"]["ok"] is False
    assert "未知工具" in outs[0]["result"]["error"]


def test_dangerous_tool_needs_approval():
    reg = ToolRegistry()
    reg.register_function("nuke", "危险", {"type": "object", "properties": {}},
                          lambda: "boom!", dangerous=True)
    # 无审批通道 → 拒绝
    ex = ToolExecutor(reg, approver=None)
    outs = asyncio.run(ex.execute_batch(
        [ToolCall(call_id="d1", name="nuke", arguments="{}")]))
    assert outs[0]["result"]["ok"] is False

    # 审批通过 → 执行
    async def ok_approver(spec, args):
        return True
    ex2 = ToolExecutor(reg, approver=ok_approver)
    outs2 = asyncio.run(ex2.execute_batch(
        [ToolCall(call_id="d2", name="nuke", arguments="{}")]))
    assert outs2[0]["result"]["ok"] is True


# --------------------------------------------------------------------- #
# 2. ask_human 分组挂起
# --------------------------------------------------------------------- #

def test_ask_human_grouping_and_pending():
    from agentprod.tools import _PendingWithResults
    reg = build_registry()
    calls = [
        ToolCall(call_id="t1", name="get_time", arguments="{}"),
        ToolCall(call_id="a1", name="ask_human",
                 arguments=json.dumps({"question": "要查哪个城市？"})),
        ToolCall(call_id="t2", name="get_time", arguments="{}"),
    ]
    ex = ToolExecutor(reg)
    with pytest.raises(_PendingWithResults) as pi:
        asyncio.run(ex.execute_batch(calls))
    # 普通工具结果已生成并携带
    ids = [r["call_id"] for r in pi.value.results]
    assert ids == ["t1", "t2"]
    assert pi.value.call_id == "a1"
    assert "城市" in pi.value.question


def test_queued_asks_serialized():
    from agentprod.tools import _PendingWithResults
    reg = build_registry()
    calls = [
        ToolCall(call_id="a1", name="ask_human",
                 arguments=json.dumps({"question": "Q1"})),
        ToolCall(call_id="a2", name="ask_human",
                 arguments=json.dumps({"question": "Q2"})),
    ]
    ex = ToolExecutor(reg)
    with pytest.raises(_PendingWithResults) as pi:
        asyncio.run(ex.execute_batch(calls))
    assert pi.value.call_id == "a1"
    queued = pi.value.meta.get("queued_asks", [])
    assert len(queued) == 1 and queued[0]["call_id"] == "a2"


# --------------------------------------------------------------------- #
# 3. Agent 主循环
# --------------------------------------------------------------------- #

def test_agent_loop_multi_tool_then_final():
    script = [
        AgentTurn(tool_calls=[
            ToolCall(call_id="1", name="get_time", arguments="{}"),
            ToolCall(call_id="2", name="calculator",
                     arguments=json.dumps({"expression": "2+3*4"})),
        ]),
        AgentTurn(text="现在是白天，2+3*4=14。"),
    ]
    agent = make_agent(script)
    out = asyncio.run(agent.run("现在几点？算 2+3*4"))
    assert "14" in out
    # messages 应包含 2 条 function_call_output
    outs = [m for m in agent.messages if m.get("type") == "function_call_output"]
    assert len(outs) == 2
    assert json.loads(outs[1]["output"])["data"] == '{"result": 14}'


def test_agent_pause_and_resume():
    script = [
        AgentTurn(tool_calls=[
            ToolCall(call_id="q1", name="ask_human",
                     arguments=json.dumps({"question": "查哪个城市？"})),
        ]),
        AgentTurn(text="收到，查北京。"),
    ]
    agent = make_agent(script)
    with pytest.raises(PauseForHuman):
        asyncio.run(agent.run("查订单"))
    assert agent.pending is not None
    out = asyncio.run(agent.resume("北京"))
    assert "北京" in out
    # resume 后 pending 清空，输出对上了 call_id
    assert agent.pending is None
    outs = [m for m in agent.messages if m.get("type") == "function_call_output"]
    assert outs[-1]["call_id"] == "q1"
    assert "北京" in outs[-1]["output"]


def test_agent_mixed_batch_pause_keeps_normal_results():
    """一批 [查时间, 问人, 算数]：普通结果先落袋，再挂起。"""
    script = [
        AgentTurn(tool_calls=[
            ToolCall(call_id="t1", name="get_time", arguments="{}"),
            ToolCall(call_id="q1", name="ask_human",
                     arguments=json.dumps({"question": "用哪种格式？"})),
            ToolCall(call_id="c1", name="calculator",
                     arguments=json.dumps({"expression": "10/4"})),
        ]),
        AgentTurn(text="好的，用 JSON 格式，10/4=2.5。"),
    ]
    agent = make_agent(script)
    with pytest.raises(PauseForHuman):
        asyncio.run(agent.run("算 10/4"))
    outs = [m for m in agent.messages if m.get("type") == "function_call_output"]
    ids = [o["call_id"] for o in outs]
    assert ids == ["t1", "c1"]          # 普通结果已入账
    out = asyncio.run(agent.resume("JSON"))
    assert "2.5" in out
    outs2 = [m for m in agent.messages if m.get("type") == "function_call_output"]
    assert [o["call_id"] for o in outs2] == ["t1", "c1", "q1"]


# --------------------------------------------------------------------- #
# 4. 上下文压缩
# --------------------------------------------------------------------- #

def test_compaction_triggers_and_keeps_structure():
    # 小窗口强制触发压缩；用大参数工具调用让上下文真实增长
    profiles = {
        "p1": ModelProfile(name="p1", model="fake-1",
                           context_window=1000, compaction_ratio=0.3),
        "p2": ModelProfile(name="p2", model="fake-2", context_window=1000,
                           is_summary_model=True),
    }
    big_args = json.dumps({"expression": "1+" + "1" * 600})   # ~600 chars
    script = []
    for i in range(5):
        script.append(AgentTurn(tool_calls=[
            ToolCall(call_id=f"c{i}", name="calculator",
                     arguments=big_args)]))
    script.append(AgentTurn(text="done"))

    agent = make_agent(script, router=make_router(script, profiles))
    out = asyncio.run(agent.run("go"))
    assert out == "done"
    assert agent.steps_used >= 5
    # 触发过压缩：出现 [历史摘要]
    joined = json.dumps([m.get("content", "") for m in agent.messages
                         if isinstance(m.get("content"), str)],
                        ensure_ascii=False)
    assert "历史摘要" in joined
    # system prompt 仍在第一条
    assert agent.messages[0]["role"] == "system"


# --------------------------------------------------------------------- #
# 5. 序列化 / 恢复
# --------------------------------------------------------------------- #

def test_state_roundtrip_and_resume_after_reload():
    script = [
        AgentTurn(tool_calls=[
            ToolCall(call_id="q1", name="ask_human",
                     arguments=json.dumps({"question": "叫什么名字？"})),
        ]),
        AgentTurn(text="你好，测试者！"),
    ]
    agent = make_agent(script)
    with pytest.raises(PauseForHuman):
        asyncio.run(agent.run("打个招呼"))

    state = agent.to_state()
    assert state["pending"]["call_id"] == "q1"

    # 重建
    from agentprod.agent import Agent
    router = make_router([AgentTurn(text="你好，测试者！")])
    cfg = AgentConfig(name="main", system_prompt="test",
                      tool_names=["get_time", "calculator", "ask_human"])
    agent2 = Agent.from_state(state, router, build_registry(),
                              {"main": cfg})
    assert agent2.pending is not None
    out = asyncio.run(agent2.resume("小明"))
    # 恢复后正常续跑出最终文本
    assert "测试者" in out
    # 用户回答已作为 function_call_output 入账且对上 call_id
    outs = [m for m in agent2.messages
            if m.get("type") == "function_call_output"]
    assert outs[-1]["call_id"] == "q1" and "小明" in outs[-1]["output"]


# --------------------------------------------------------------------- #
# 6. SQL 只读防护
# --------------------------------------------------------------------- #

def test_sql_guard():
    demo_db.init_demo_db()
    r = json.loads(builtin_tools.run_sql("DELETE FROM users"))
    assert "error" in r
    r2 = json.loads(builtin_tools.run_sql("SELECT 1"))
    assert "rows" in r2
    # 强制 LIMIT：查全表也不爆
    r3 = json.loads(builtin_tools.run_sql("SELECT * FROM orders"))
    assert r3["row_count"] <= 200


def test_sql_valid_aggregate():
    demo_db.init_demo_db()
    r = json.loads(builtin_tools.run_sql(
        "SELECT city, COUNT(*) n FROM users GROUP BY city ORDER BY n DESC"))
    assert r["row_count"] >= 1


# --------------------------------------------------------------------- #
# 7. 配置与模型切换
# --------------------------------------------------------------------- #

def test_load_configs():
    from agentprod.config import load_model_profiles, load_agent_configs
    profiles, default, summary = load_model_profiles()
    assert default in profiles
    assert summary in profiles
    agents = load_agent_configs()
    assert "main" in agents and "researcher" in agents
    assert "ask_human" in agents["main"].tool_names


def test_switch_model_session_level():
    script = [AgentTurn(text="ok")]
    agent = make_agent(script)
    r = json.loads(agent.switch_model("p2"))
    assert r["ok"] is True and r["data"]["to"] == "p2"
    r2 = json.loads(agent.switch_model("no-such"))
    assert r2["ok"] is False


# --------------------------------------------------------------------- #
# 8. spawn
# --------------------------------------------------------------------- #

def test_spawn_child_noninteractive():
    from agentprod.agent import Agent
    from agentprod.runtime import Runtime

    rt = Runtime.__new__(Runtime)  # 不跑 __init__（避免读配置文件依赖）
    # 手工搭最小运行时
    profiles = {
        "p1": ModelProfile(name="p1", model="fake-1"),
        "p2": ModelProfile(name="p2", model="fake-2", is_summary_model=True),
    }
    rt.router = LLMRouter(profiles, "p1", "p2")
    rt.router._clients["p1"] = _ClientWrap(FakeLLMClient(
        [AgentTurn(text="子任务完成：结论A")]))
    rt.router._clients["p2"] = _ClientWrap(FakeLLMClient(
        [AgentTurn(text="摘要")]))
    rt.agent_configs = {
        "researcher": AgentConfig(name="researcher",
                                  system_prompt="调研",
                                  tool_names=["get_time"],
                                  interactive=False),
    }
    rt.registry = build_registry()

    parent_cfg = AgentConfig(name="main", system_prompt="主",
                             tool_names=["get_time"], can_spawn=True,
                             spawn_depth_max=2)
    parent = Agent(parent_cfg, rt.router, rt.registry,
                   spawn_factory=lambda name, depth=0: Agent(
                       rt.agent_configs[name], rt.router, rt.registry,
                       depth=depth))
    try:
        out = asyncio.run(parent.spawn("researcher", "查点什么"))
        d = json.loads(out)
        assert d["ok"] is True and "结论A" in d["data"]
        # 深度限制
        child = Agent(rt.agent_configs["researcher"], rt.router,
                      rt.registry, depth=2,
                      spawn_factory=lambda name, depth=0: Agent(
                          rt.agent_configs[name], rt.router, rt.registry,
                          depth=depth))
        child.cfg.can_spawn = True
        out2 = asyncio.run(child.spawn("researcher", "再套一层"))
        assert json.loads(out2)["ok"] is False
    finally:
        pass


if __name__ == "__main__":
    sys.exit(pytest.main([__file__, "-v"]))
