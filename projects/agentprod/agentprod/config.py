"""配置加载：模型配置(models.yaml) + Agent 角色配置(agents.yaml)。

核心思想：Agent = 一份配置。新增角色不改代码，只加 YAML 条目。
模型也是配置：多模型档案、运行时可切换。
"""
from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import yaml

ROOT = Path(__file__).resolve().parent.parent
CONFIG_DIR = ROOT / "config"
DATA_DIR = ROOT / "data"


@dataclass
class ModelProfile:
    """一个模型档案 = 连接参数 + 采样参数 + 上下文窗口信息。"""
    name: str                      # 档案名（切换时用它，如 "gpt-4o-mini"）
    model: str                     # 真正发给 API 的 model id
    api_key_env: str = "OPENAI_API_KEY"
    base_url_env: Optional[str] = None   # 兼容网关（DeepSeek/本地 vLLM 等）
    temperature: float = 0.3
    max_output_tokens: int = 2048
    context_window: int = 128000    # 用于估算压缩阈值
    compaction_ratio: float = 0.7   # 超过窗口 70% 触发压缩
    is_summary_model: bool = False  # 压缩摘要用的廉价模型
    protocol: str = "responses"     # responses | chat-completions（协议适配）

    @property
    def api_key(self) -> str:
        return os.environ.get(self.api_key_env, "")

    @property
    def base_url(self) -> Optional[str]:
        if self.base_url_env:
            return os.environ.get(self.base_url_env)
        return os.environ.get("OPENAI_BASE_URL") or None


@dataclass
class AgentConfig:
    """一个 Agent 角色 = system prompt + 工具清单 + 限制。"""
    name: str
    system_prompt: str
    tool_names: list = field(default_factory=list)
    max_steps: int = 20
    interactive: bool = True          # 是否能用 ask_human 直接问用户
    can_spawn: bool = False           # 是否能 spawn 子 agent
    can_switch_model: bool = False    # 是否能自己切换模型
    emit_progress: bool = True        # 是否向聊天口播报工具调用进度
    model: Optional[str] = None       # 角色默认模型（缺省用全局默认）
    spawn_max_parallel: int = 4       # 并行子 agent 上限
    spawn_depth_max: int = 2          # 子 agent 递归深度上限


def _load_yaml(path: Path) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_model_profiles(path: Path = None) -> tuple:
    """返回 (profiles_dict, default_name, summary_name)。"""
    path = path or (CONFIG_DIR / "models.yaml")
    raw = _load_yaml(path)
    profiles = {}
    for item in raw.get("models", []):
        p = ModelProfile(
            name=item["name"],
            model=item.get("model", item["name"]),
            api_key_env=item.get("api_key_env", "OPENAI_API_KEY"),
            base_url_env=item.get("base_url_env"),
            temperature=float(item.get("temperature", 0.3)),
            max_output_tokens=int(item.get("max_output_tokens", 2048)),
            context_window=int(item.get("context_window", 128000)),
            compaction_ratio=float(item.get("compaction_ratio", 0.7)),
            is_summary_model=bool(item.get("summary", False)),
            protocol=item.get("protocol", "responses"),
        )
        profiles[p.name] = p
    default_name = raw.get("default") or next(iter(profiles), None)
    if default_name not in profiles:
        raise ValueError(f"models.yaml: default 模型 {default_name!r} 不存在")
    summary_name = raw.get("summary_model") or next(
        (n for n, p in profiles.items() if p.is_summary_model), default_name)
    return profiles, default_name, summary_name


def load_agent_configs(path: Path = None) -> dict:
    """返回 {name: AgentConfig}。"""
    path = path or (CONFIG_DIR / "agents.yaml")
    raw = _load_yaml(path)
    configs = {}
    for name, item in raw.items():
        configs[name] = AgentConfig(
            name=name,
            system_prompt=item.get("system_prompt", "你是一个有用的助手。"),
            tool_names=item.get("tools", []),
            max_steps=int(item.get("max_steps", 20)),
            interactive=bool(item.get("interactive", True)),
            can_spawn=bool(item.get("can_spawn", False)),
            can_switch_model=bool(item.get("can_switch_model", False)),
            emit_progress=bool(item.get("emit_progress", True)),
            model=item.get("model"),
            spawn_max_parallel=int(item.get("spawn_max_parallel", 4)),
            spawn_depth_max=int(item.get("spawn_depth_max", 2)),
        )
    return configs
