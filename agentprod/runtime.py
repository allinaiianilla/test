"""运行时组装：注册表 + 路由器 + 会话管理。

会话层设计（讨论过的"同一条电话线"）：
- 用户消息进 Session.on_message()
- 无 pending → agent.run()（新任务）
- 有 pending → agent.resume()（回答上一问）→ 可能再抛新问题
- 崩溃恢复：agent 状态落盘 JSON，进程重启后 SessionStore.load 重建
"""
from __future__ import annotations

import json
import threading
import time
import uuid
from pathlib import Path
from typing import Optional

from .agent import Agent, PendingAsk
from .binding import bind_session_tools  # noqa: F401  (补丁副作用导入)
from .config import (DATA_DIR, AgentConfig, ModelProfile, load_agent_configs,
                     load_model_profiles)
from .llm import LLMRouter
from .tools import PauseForHuman, ToolRegistry, ToolSpec
from . import builtin_tools


# ---------------------------------------------------------------------- #
# 会话存储
# ---------------------------------------------------------------------- #

class SessionStore:
    """会话与 agent 状态持久化（JSON 文件，生产可换 Redis/PG）。"""

    def __init__(self, root: Path = None):
        self.root = root or (DATA_DIR / "sessions")
        self.root.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def _path(self, sid: str) -> Path:
        safe = "".join(c for c in sid if c.isalnum() or c in "-_")
        return self.root / f"{safe}.json"

    def save(self, sid: str, state: dict):
        with self._lock:
            tmp = self._path(sid).with_suffix(".tmp")
            tmp.write_text(json.dumps(state, ensure_ascii=False, indent=1),
                           encoding="utf-8")
            tmp.replace(self._path(sid))

    def load(self, sid: str) -> Optional[dict]:
        p = self._path(sid)
        if not p.exists():
            return None
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:  # noqa: BLE001
            return None

    def save_agent_state(self, agent: Agent):
        """供 agent._persist 回调（sid 由 agent._bound_sid 携带）。"""
        sid = getattr(agent, "_bound_sid", None)
        if sid:
            self.save(sid, agent.to_state())

    def delete(self, sid: str):
        p = self._path(sid)
        if p.exists():
            p.unlink()


# ---------------------------------------------------------------------- #
# 会话
# ---------------------------------------------------------------------- #

class Session:
    """一个用户会话 = 一个主 Agent 实例 + 消息历史 + 挂起状态。

    对外只暴露 on_message(text) -> SessionReply。
    """

    def __init__(self, sid: str, agent: Agent, store: SessionStore):
        self.sid = sid
        self.agent = agent
        self.store = store
        agent._bound_sid = sid             # 绑定持久化目标
        self.created_at = time.time()
        self.last_active = time.time()

    async def on_message(self, text: str) -> "SessionReply":
        """聊天入口：按 pending 状态路由（正常聊天/回答问题同一口）。"""
        self.last_active = time.time()
        try:
            if self.agent.pending:
                answer = await self.agent.resume(text)
            else:
                answer = await self.agent.run(text)
            return SessionReply(sid=self.sid, kind="final", text=answer,
                                pending_question=None)
        except PauseForHuman as p:
            return SessionReply(sid=self.sid, kind="ask",
                                text=p.question,
                                pending_question=p.question)
        except Exception as e:  # noqa: BLE001
            return SessionReply(sid=self.sid, kind="error",
                                text=f"内部错误: {e}", pending_question=None)


class SessionReply:
    def __init__(self, sid: str, kind: str, text: str, pending_question):
        self.sid = sid
        self.kind = kind        # final | ask | error
        self.text = text
        self.pending_question = pending_question

    def to_dict(self) -> dict:
        return {"sid": self.sid, "kind": self.kind,
                "reply": self.text,
                "pending": bool(self.pending_question)}


# ---------------------------------------------------------------------- #
# 运行时（组装根）
# ---------------------------------------------------------------------- #

class Runtime:
    """全局单例：注册表、模型路由、agent 配置、会话表。"""

    def __init__(self, config_dir: Path = None):
        # 兼容「目录下有 config/」和「直接传 models.yaml 路径」两种用法
        if config_dir is not None and config_dir.is_file():
            config_dir = config_dir.parent
        self.model_profiles, self.default_model, self.summary_model = \
            load_model_profiles(
                config_dir / "models.yaml" if config_dir else None)
        self.agent_configs: dict = load_agent_configs(
            config_dir / "agents.yaml" if config_dir else None)
        self.router = LLMRouter(self.model_profiles,
                                self.default_model, self.summary_model)
        self.registry = ToolRegistry()

        builtin_tools.register_builtin_tools(
            self.registry,
            spawn_impl=_placeholder_spawn,       # 绑定层会按会话覆盖
            switch_impl=_placeholder_switch,
            list_models_impl=self._list_models_impl(),
        )
        self.store = SessionStore()
        self.sessions: dict = {}
        self._sessions_lock = threading.Lock()

    # ---------- agent 工厂（spawn 与恢复共用） ----------

    def build_agent(self, role: str, depth: int = 0,
                    model_profile: str = None) -> Agent:
        cfg = self.agent_configs[role]
        return Agent(cfg, self.router, self.registry,
                     depth=depth, model_profile=model_profile,
                     executor_kwargs={"approver": self._approver,
                                      "progress": self._progress},
                     session_store=None,          # 子 agent 不落盘
                     spawn_factory=self.build_agent)

    def build_session_agent(self, role: str, sid: str) -> Agent:
        """主会话 agent：带持久化绑定。"""
        cfg = self.agent_configs[role]
        agent = Agent(cfg, self.router, self.registry,
                      executor_kwargs={"approver": self._approver,
                                       "progress": self._progress},
                      session_store=self.store,
                      spawn_factory=self.build_agent)
        agent._bound_sid = sid
        return agent

    # ---------- 会话管理 ----------

    def get_or_create_session(self, sid: str = None,
                              role: str = "main") -> Session:
        sid = sid or f"sess_{uuid.uuid4().hex[:12]}"
        with self._sessions_lock:
            if sid in self.sessions:
                return self.sessions[sid]
            state = self.store.load(sid)
            if state:
                agent = Agent.from_state(
                    state, self.router, self.registry, self.agent_configs,
                    session_store=self.store,
                    spawn_factory=self.build_agent)
                agent._bound_sid = sid
            else:
                agent = self.build_session_agent(role, sid)
            sess = Session(sid, agent, self.store)
            self.sessions[sid] = sess
            return sess

    def close_session(self, sid: str):
        with self._sessions_lock:
            self.sessions.pop(sid, None)
            self.store.delete(sid)

    def list_sessions(self) -> list:
        return [{"sid": s.sid, "created_at": s.created_at,
                 "last_active": s.last_active,
                 "pending": bool(s.agent.pending),
                 "role": s.agent.cfg.name,
                 "model": s.agent.model_profile}
                for s in self.sessions.values()]

    def switch_session_model(self, sid: str, profile: str) -> dict:
        sess = self.sessions.get(sid) or self.get_or_create_session(sid)
        result = json.loads(sess.agent.switch_model(profile))
        return result

    # ---------- 审批/进度（默认实现，可注入覆盖） ----------

    async def _approver(self, spec: ToolSpec, args: dict) -> bool:
        """默认审批：无 UI 桥时危险工具默认拒绝（安全优先）。"""
        return False

    async def _progress(self, spec: ToolSpec, args: dict):
        pass

    def set_interaction(self, approver=None, progress=None):
        """注入自定义审批/进度（CLI / API 各自注入）。

        只影响之后新建的 agent；已有会话在下一轮工具批执行时生效
        （executor_kwargs 引用同一 dict）。
        """
        if approver is not None:
            self._approver = approver
        if progress is not None:
            self._progress = progress

    # ---------- 模型列表工具实现 ----------

    def _list_models_impl(self):
        def list_models() -> str:
            items = []
            for n, p in self.model_profiles.items():
                items.append({
                    "profile": n, "model": p.model,
                    "summary": p.is_summary_model,
                    "context_window": p.context_window,
                    "default": n == self.router.default_name,
                })
            return json.dumps({"models": items,
                               "default": self.router.default_name,
                               "summary_model": self.router.summary_model},
                              ensure_ascii=False)
        return list_models


# 占位实现：真实逻辑由 binding.py 在 executor 构建时按 agent 绑定替换
async def _placeholder_spawn(agent_name: str, task: str) -> str:
    return json.dumps({"ok": False, "error": "spawn 未绑定会话"})


async def _placeholder_switch(profile: str) -> str:
    return json.dumps({"ok": False, "error": "switch_model 未绑定会话"})
