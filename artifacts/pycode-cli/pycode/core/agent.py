"""
Agent 核心引擎 — ReAct (Reasoning + Acting) 模式的实现。

工作流程:
1. 接收用户输入
2. LLM 思考 → 是否需要调用工具？
3. 如果需要 → 执行工具 → 把结果反馈给 LLM → 回到 2
4. 如果不需要 → 直接返回回答

最大轮数限制防止无限循环。
"""

import json
import re
import traceback
from typing import Callable, Iterator, Optional

from ..llm import BaseLLM
from ..tools import ToolRegistry
from ..config import Config
from .context import ConversationContext
from .prompt import (
    build_system_prompt,
    format_user_message,
    format_tool_result,
)


class AgentState:
    """Agent 运行状态"""
    IDLE = "idle"
    THINKING = "thinking"
    TOOL_CALL = "tool_call"
    DONE = "done"
    ERROR = "error"


class Agent:
    """
    PyCode Agent 主引擎。

    采用 ReAct 模式：反复「思考 → 行动 → 观察」直到完成任务。

    用法::

        from pycode.llm import OpenAICompatibleLLM
        from pycode.core import Agent

        llm = OpenAICompatibleLLM(api_key="...")
        agent = Agent(llm)

        # 单次任务
        answer = agent.run("给我写一个快速排序")

        # 流式任务
        for chunk in agent.run_stream("分析这个项目的代码质量"):
            print(chunk, end="")

        # 交互式对话
        agent.chat("看看 main.py")    # 会维护上下文
        agent.chat("给它加个注释")    # 记住上一条
    """

    def __init__(
        self,
        llm: BaseLLM,
        config: Optional[Config] = None,
        tools: Optional[ToolRegistry] = None,
        on_confirm: Optional[Callable[[str], bool]] = None,
    ):
        """
        Args:
            llm: LLM 实例
            config: 配置对象，None 则用默认
            tools: 工具注册中心，None 则用内置工具
            on_confirm: 危险操作确认回调，返回 True 才继续
        """
        self._llm = llm
        self._config = config or Config.load()
        self._registry = tools or self._build_default_tools()
        self._on_confirm = on_confirm or self._default_confirm
        self._context = ConversationContext(
            max_messages=self._config.agent.max_turns * 2
        )
        self.state = AgentState.IDLE

        # 构建 system prompt
        self._context.add_system(
            build_system_prompt(
                self._registry,
                workspace=self._config.tools.workspace,
            )
        )

    # ---- 公共接口 ----
    def run(self, query: str) -> str:
        """
        执行一次任务（非流式）。

        Args:
            query: 用户输入

        Returns:
            Agent 的最终回复
        """
        self._context.add_user(query)
        return self._react_loop()

    def run_stream(self, query: str) -> Iterator[str]:
        """
        执行任务（流式输出）。

        Args:
            query: 用户输入

        Yields:
            文本片段
        """
        self._context.add_user(query)
        yield from self._react_loop_stream()

    def chat(self, query: str) -> str:
        """
        交互式对话（维护上下文，不执行工具循环）。
        适合已经进入对话状态后的连续交互。

        Args:
            query: 用户输入

        Returns:
            助手回复
        """
        self._context.add_user(query)
        messages = self._context.get_messages()
        try:
            reply = self._llm.chat(messages)
            self._context.add_assistant(reply)
            return reply
        except Exception as e:
            self.state = AgentState.ERROR
            return f"❌ 调用失败: {e}"

    def reset(self) -> None:
        """重置对话上下文"""
        self._context.clear(keep_system=True)
        self.state = AgentState.IDLE

    # ---- ReAct 核心循环 ----
    def _react_loop(self) -> str:
        """ReAct 循环：反复思考 → 行动 → 观察"""
        max_turns = self._config.agent.max_turns
        final_answer = ""

        for turn in range(max_turns):
            self.state = AgentState.THINKING
            messages = self._context.get_messages()

            try:
                reply = self._llm.chat(messages)
            except Exception as e:
                self.state = AgentState.ERROR
                return f"❌ LLM 调用失败: {e}"

            # 检查是否包含工具调用
            tool_calls = self._parse_tool_calls(reply)

            if not tool_calls:
                # 没有工具调用 → 这就是最终回答
                self.state = AgentState.DONE
                self._context.add_assistant(reply)
                return reply

            # 有工具调用 → 逐个执行
            self.state = AgentState.TOOL_CALL
            tool_results = []
            for tc in tool_calls:
                result = self._execute_tool(tc["name"], tc["arguments"])
                tool_results.append(format_tool_result(tc["name"], result))

            # 把工具结果反馈给 LLM
            self._context.add_assistant(reply)
            for tr in tool_results:
                self._context.add_tool_result("工具", tr)

        # 超出最大轮数
        self.state = AgentState.DONE
        return self._llm.chat(self._context.get_messages())

    def _react_loop_stream(self) -> Iterator[str]:
        """ReAct 循环的流式版本"""
        max_turns = self._config.agent.max_turns

        for turn in range(max_turns):
            self.state = AgentState.THINKING
            messages = self._context.get_messages()

            # 收集完整回复（流式输出给用户）
            full_reply = ""
            try:
                for chunk in self._llm.chat_stream(messages):
                    full_reply += chunk
                    yield chunk
            except Exception as e:
                yield f"\n❌ {e}"
                return

            # 检查工具调用
            tool_calls = self._parse_tool_calls(full_reply)
            if not tool_calls:
                self.state = AgentState.DONE
                self._context.add_assistant(full_reply)
                return

            # 执行工具
            self.state = AgentState.TOOL_CALL
            status = f"\n\n🔧 调用 {len(tool_calls)} 个工具...\n"
            yield status

            self._context.add_assistant(full_reply)
            for tc in tool_calls:
                result = self._execute_tool(tc["name"], tc["arguments"])
                self._context.add_tool_result(tc["name"], result)

        yield "\n⚠️ 达到最大思考轮数，总结中...\n"
        final = self._llm.chat(self._context.get_messages())
        yield final

    # ---- 工具调用解析与执行 ----
    def _parse_tool_calls(self, reply: str) -> list[dict]:
        """
        解析 LLM 回复中的工具调用。

        支持格式：
        ```tool_call
        {"name": "xxx", "arguments": {...}}
        ```
        """
        # 匹配 code block 中的 tool_call
        pattern = r'```tool_call\s*\n(.*?)\n```'
        matches = re.findall(pattern, reply, re.DOTALL)
        calls = []
        for m in matches:
            try:
                call = json.loads(m.strip())
                if "name" in call and "arguments" in call:
                    calls.append(call)
            except json.JSONDecodeError:
                continue
        return calls

    def _execute_tool(self, name: str, arguments: dict) -> str:
        """
        执行工具调用（含危险操作确认）。

        Args:
            name: 工具名
            arguments: 参数字典

        Returns:
            工具执行结果
        """
        tool = self._registry.get(name)
        if not tool:
            return f"未知工具: {name}"

        # 危险操作需确认
        if tool.dangerous:
            confirm_msg = f"⚠️ Agent 请求执行危险操作:\n  {name}({arguments})\n是否允许？(y/n)"
            if not self._on_confirm(confirm_msg):
                return f"用户取消了操作: {name}"

        return self._registry.execute(name, arguments)

    # ---- 默认工具注册 ----
    @staticmethod
    def _build_default_tools() -> ToolRegistry:
        """构建默认工具集"""
        from ..tools import register_builtin_tools
        registry = ToolRegistry()
        register_builtin_tools(registry)
        return registry

    @staticmethod
    def _default_confirm(msg: str) -> bool:
        """默认的确认处理（非交互模式默认允许）"""
        return True

    def __repr__(self) -> str:
        return (f"Agent(llm={self._llm.model_name}, "
                f"tools={len(self._registry)}, "
                f"state={self.state})")
