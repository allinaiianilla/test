"""
LLM 抽象基类 — 定义统一的 LLM 调用接口。

所有 LLM 实现必须继承 BaseLLM 并实现 chat/chat_stream 方法。
"""

from abc import ABC, abstractmethod
from typing import Iterator, Optional


class BaseLLM(ABC):
    """
    LLM 统一抽象接口。

    设计理念：
    - 单一职责：只负责"发送消息 → 返回文本"
    - 工具调用、上下文管理都在 Agent 层处理
    - 子类只需实现两个方法：chat 和 chat_stream

    用法::

        llm = OpenAICompatibleLLM(api_key="...", model="gpt-4o")
        answer = llm.chat([
            {"role": "system", "content": "你是代码助手"},
            {"role": "user", "content": "写一个冒泡排序"}
        ])
        print(answer)
    """

    @abstractmethod
    def chat(self, messages: list[dict]) -> str:
        """
        发送消息并获取完整回复。

        Args:
            messages: 消息列表，格式为 [{"role": str, "content": str}, ...]

        Returns:
            LLM 的文本回复
        """
        ...

    @abstractmethod
    def chat_stream(self, messages: list[dict]) -> Iterator[str]:
        """
        流式发送消息，逐 token 返回。

        Args:
            messages: 消息列表

        Yields:
            文本片段（每次一个或多个 token）
        """
        ...

    @property
    @abstractmethod
    def model_name(self) -> str:
        """返回当前使用的模型名称"""
        ...

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(model={self.model_name})"


class LLMError(Exception):
    """LLM 调用相关异常"""
    pass


class LLMTimeoutError(LLMError):
    """LLM 调用超时"""
    pass


class LLMAuthError(LLMError):
    """认证失败（API Key 无效）"""
    pass
