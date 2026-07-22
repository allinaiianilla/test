"""
配置管理模块。
支持层级加载：环境变量 > 用户配置文件 > 默认值。

配置路径优先级:
1. PYCODE_CONFIG 环境变量指定的路径
2. ~/.pycode/config.yaml
3. 项目目录下的 .pycode.yaml
4. 默认值
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

# ============================================================
# 默认配置
# ============================================================
DEFAULT_CONFIG = {
    "llm": {
        "provider": "openai_compat",
        "api_key": "",          # 从环境变量 PYCODE_API_KEY 读取
        "base_url": "https://api.openai.com/v1",
        "model": "gpt-4o-mini",
        "max_tokens": 4096,
        "temperature": 0.7,
    },
    "tools": {
        "allow_shell": False,   # 安全：默认不允许执行 Shell 命令
        "allow_write": True,
        "allow_exec": False,    # 安全：默认不允许执行任意 Python
        "workspace": ".",       # 工作目录
    },
    "ui": {
        "stream": True,         # 流式输出
        "color": True,          # 彩色输出
        "verbose": False,       # 详细日志
    },
    "agent": {
        "max_turns": 10,        # Agent 最大思考轮数
        "context_lines": 50,    # 读取文件时的上下文行数
    }
}


@dataclass
class LLMConfig:
    """LLM 配置"""
    provider: str = "openai_compat"
    api_key: str = ""
    base_url: str = "https://api.openai.com/v1"
    model: str = "gpt-4o-mini"
    max_tokens: int = 4096
    temperature: float = 0.7


@dataclass
class ToolsConfig:
    """工具权限配置"""
    allow_shell: bool = False
    allow_write: bool = True
    allow_exec: bool = False
    workspace: str = "."


@dataclass
class UIConfig:
    """UI 配置"""
    stream: bool = True
    color: bool = True
    verbose: bool = False


@dataclass
class AgentConfig:
    """Agent 配置"""
    max_turns: int = 10
    context_lines: int = 50


@dataclass
class Config:
    """
    全局配置对象。
    用法: config = Config.load()
    """
    llm: LLMConfig = field(default_factory=LLMConfig)
    tools: ToolsConfig = field(default_factory=ToolsConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)

    @classmethod
    def load(cls, config_path: Optional[str] = None) -> "Config":
        """
        加载配置。
        优先级: 环境变量 > 文件 > 默认值
        """
        config = cls()

        # 1. 加载默认值
        merged = dict(DEFAULT_CONFIG)

        # 2. 尝试从文件加载
        file_config = cls._load_file(config_path)
        if file_config:
            cls._deep_merge(merged, file_config)

        # 3. 环境变量覆盖
        if os.environ.get("PYCODE_API_KEY"):
            merged["llm"]["api_key"] = os.environ["PYCODE_API_KEY"]
        if os.environ.get("PYCODE_MODEL"):
            merged["llm"]["model"] = os.environ["PYCODE_MODEL"]
        if os.environ.get("PYCODE_BASE_URL"):
            merged["llm"]["base_url"] = os.environ["PYCODE_BASE_URL"]
        if os.environ.get("PYCODE_WORKSPACE"):
            merged["tools"]["workspace"] = os.environ["PYCODE_WORKSPACE"]

        # 4. 应用到 config 对象
        config.llm = LLMConfig(**merged["llm"])
        config.tools = ToolsConfig(**merged["tools"])
        config.ui = UIConfig(**merged["ui"])
        config.agent = AgentConfig(**merged["agent"])

        return config

    @staticmethod
    def _load_file(path: Optional[str] = None) -> Optional[dict]:
        """从文件加载配置（JSON 或 YAML 简化版）"""
        candidates = []

        if path:
            candidates.append(Path(path))
        if os.environ.get("PYCODE_CONFIG"):
            candidates.append(Path(os.environ["PYCODE_CONFIG"]))

        # 默认搜索路径
        home_config = Path.home() / ".pycode" / "config.json"
        project_config = Path.cwd() / ".pycode.json"

        candidates.extend([home_config, project_config])

        for p in candidates:
            if p.exists():
                try:
                    with open(p, encoding="utf-8") as f:
                        return json.load(f)
                except (json.JSONDecodeError, OSError):
                    continue
        return None

    @staticmethod
    def _deep_merge(base: dict, override: dict) -> None:
        """递归合并 override 到 base"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                Config._deep_merge(base[key], value)
            else:
                base[key] = value

    def to_dict(self) -> dict:
        """转为字典"""
        return {
            "llm": asdict(self.llm),
            "tools": asdict(self.tools),
            "ui": asdict(self.ui),
            "agent": asdict(self.agent),
        }

    def save(self, path: str) -> None:
        """保存配置到文件"""
        with open(path, "w", encoding="utf-8") as f:
            json.dump(self.to_dict(), f, indent=2, ensure_ascii=False)
