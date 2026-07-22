"""
工具注册中心 — 管理所有可用工具。

设计理念：
- 工具 = 名称 + 描述 + JSON Schema参数 + Python函数
- 注册中心负责：注册 → 生成 prompt → 解析调用 → 调度执行
"""

import json
import traceback
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


@dataclass
class Tool:
    """
    一个可用工具的定义。

    用法::

        def read_file(path: str) -> str:
            return Path(path).read_text()

        tool = Tool(
            name="read_file",
            description="读取文件内容",
            parameters={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "文件路径"}
                },
                "required": ["path"]
            },
            function=read_file,
            dangerous=False,
        )
    """
    name: str
    description: str
    parameters: dict          # JSON Schema 格式
    function: Callable        # 实际执行函数
    dangerous: bool = False   # 是否需要用户确认


class ToolRegistry:
    """
    工具注册中心。

    用法::

        registry = ToolRegistry()
        registry.register(read_file_tool)
        registry.register(write_file_tool)

        # 生成 prompt 给 LLM
        prompt = registry.tools_prompt()

        # 执行 LLM 返回的工具调用
        result = registry.execute("read_file", {"path": "test.py"})
    """

    def __init__(self):
        self._tools: Dict[str, Tool] = {}

    # ---- 注册 ----
    def register(self, tool: Tool) -> None:
        """注册一个工具（同名会覆盖）"""
        self._tools[tool.name] = tool

    def unregister(self, name: str) -> None:
        """注销一个工具"""
        self._tools.pop(name, None)

    # ---- 查询 ----
    def get(self, name: str) -> Optional[Tool]:
        """获取工具定义"""
        return self._tools.get(name)

    def list(self) -> List[Tool]:
        """列出所有工具"""
        return list(self._tools.values())

    def list_dangerous(self) -> List[Tool]:
        """列出需要确认的危险工具"""
        return [t for t in self._tools.values() if t.dangerous]

    # ---- Prompt 生成 ----
    def tools_prompt(self) -> str:
        """
        生成工具列表 prompt，用于注入 system message。

        格式示例::

            ## 可用工具
            1. read_file — 读取文件内容
               参数: {"path": "文件路径"}
        """
        if not self._tools:
            return ""

        lines = ["\n## 可用工具\n"]
        for i, tool in enumerate(self._tools.values(), 1):
            lines.append(f"{i}. **{tool.name}** — {tool.description}")
            # 提取参数说明
            props = tool.parameters.get("properties", {})
            required = tool.parameters.get("required", [])
            for param_name, param_info in props.items():
                desc = param_info.get("description", "")
                req_mark = " (必填)" if param_name in required else ""
                lines.append(f"   - `{param_name}`{req_mark}: {desc}")
            if tool.dangerous:
                lines.append(f"   ⚠️ 危险操作，需用户确认")
            lines.append("")
        return "\n".join(lines)

    # ---- 执行 ----
    def execute(self, name: str, arguments: dict) -> str:
        """
        执行一个工具调用。

        Args:
            name: 工具名
            arguments: 参数字典

        Returns:
            执行结果（字符串），失败时返回错误信息
        """
        tool = self._tools.get(name)
        if not tool:
            return f"错误: 未知工具 '{name}'"

        try:
            result = tool.function(**arguments)
            return str(result)
        except Exception as e:
            return f"工具 '{name}' 执行失败: {e}\n{traceback.format_exc()[-500:]}"

    # ---- 序列化 ----
    def to_openai_format(self) -> List[dict]:
        """转为 OpenAI function calling 格式"""
        tools = []
        for tool in self._tools.values():
            tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.parameters,
                }
            })
        return tools

    def __len__(self) -> int:
        return len(self._tools)

    def __contains__(self, name: str) -> bool:
        return name in self._tools
