"""Agent 与工具的绑定补丁：spawn/switch_model/ask_human 需要"当前 agent"。

Agent._make_executor 被打补丁：每次构建执行器时，把注册表复制成
"会话绑定视图"：
- spawn_agent → 当前 agent.spawn（仅 can_spawn 角色）
- switch_model → 当前 agent.switch_model（dangerous → 走审批）
- ask_human 仅交互式、顶层 agent 可见（子 agent 自动摘除）
无权限的工具连 schema 都不暴露给模型（最小暴露面）。
"""
from __future__ import annotations

from .agent import Agent
from .tools import ToolExecutor, ToolRegistry, ToolSpec


def bind_session_tools(agent: Agent) -> ToolRegistry:
    """返回一个绑定了当前 agent 的注册表视图。"""
    reg = ToolRegistry()
    base: ToolRegistry = agent.registry
    for name in base.names():
        spec = base.get(name)
        if name == "spawn_agent":
            if agent.cfg.can_spawn and agent._spawn_factory is not None:
                reg.register(ToolSpec(
                    name="spawn_agent", description=spec.description,
                    parameters=spec.parameters,
                    func=_make_spawn_func(agent),
                    timeout=600.0, group="orchestration"))
        elif name == "switch_model":
            if agent.cfg.can_switch_model:
                reg.register(ToolSpec(
                    name="switch_model", description=spec.description,
                    parameters=spec.parameters,
                    func=_make_switch_func(agent),
                    dangerous=True, group="system"))
        elif name == "ask_human":
            if agent.cfg.interactive and agent.depth == 0:
                reg.register(spec)
        else:
            reg.register(spec)
    return reg


def _make_spawn_func(agent: Agent):
    async def spawn_agent(agent_name: str, task: str) -> str:
        return await agent.spawn(agent_name, task)
    return spawn_agent


def _make_switch_func(agent: Agent):
    async def switch_model(profile: str) -> str:
        return agent.switch_model(profile)
    return switch_model


# ---- 给 Agent 打补丁：_make_executor 返回绑定视图 ----

def _patched_make_executor(self: Agent) -> ToolExecutor:
    kw = dict(self._executor_kwargs)
    reg = bind_session_tools(self)
    return ToolExecutor(reg,
                        approver=kw.get("approver"),
                        progress=kw.get("progress"),
                        ask_handler=None)


Agent._make_executor = _patched_make_executor
