"""
对话上下文管理 — 维护多轮对话历史，控制 token 用量。

设计理念：
- messages 是标准的 [{"role": str, "content": str}, ...] 格式
- 自动截断过长的历史，保留 system prompt
- 提供便捷的添加/获取/统计方法
"""

from typing import List, Optional


class ConversationContext:
    """
    对话上下文管理器。

    用法::

        ctx = ConversationContext(max_messages=20)
        ctx.add_system("你是代码助手")
        ctx.add_user("写一个排序函数")
        ctx.add_assistant("这是冒泡排序的实现...")
        messages = ctx.get_messages()  # 发给 LLM
    """

    def __init__(self, max_messages: int = 30, max_tokens_estimate: int = 8000):
        """
        Args:
            max_messages: 最大保留消息数（超出后自动裁剪）
            max_tokens_estimate: 最大估算 token 数
        """
        self._messages: list[dict] = []
        self._max_messages = max_messages
        self._max_tokens = max_tokens_estimate
        self._system_message: Optional[dict] = None

    # ---- 添加消息 ----
    def add_system(self, content: str) -> None:
        """设置 system prompt（会替换旧的）"""
        self._system_message = {"role": "system", "content": content}

    def add_user(self, content: str) -> None:
        """添加用户消息"""
        self._messages.append({"role": "user", "content": content})
        self._trim()

    def add_assistant(self, content: str) -> None:
        """添加助手回复"""
        self._messages.append({"role": "assistant", "content": content})
        self._trim()

    def add_tool_result(self, tool_name: str, result: str) -> None:
        """添加工具调用结果（用 assistant role 承载）"""
        self._messages.append({
            "role": "user",
            "content": f"[工具 {tool_name} 返回结果]:\n{result}"
        })
        self._trim()

    # ---- 获取消息 ----
    def get_messages(self) -> list[dict]:
        """获取完整的消息列表（发给 LLM）"""
        result = []
        if self._system_message:
            result.append(dict(self._system_message))
        result.extend(self._messages)
        return result

    def get_last_n(self, n: int) -> list[dict]:
        """获取最近 n 条消息（不含 system）"""
        return self._messages[-n:]

    # ---- 查询 ----
    @property
    def message_count(self) -> int:
        return len(self._messages)

    @property
    def estimated_tokens(self) -> int:
        """粗略估算 token 数（中文约 1 字=1.5 token，英文约 1 字=0.75 token）"""
        total = 0
        for msg in self._messages:
            content = msg.get("content", "")
            total += len(content) * 1.2  # 简单估算
        if self._system_message:
            total += len(self._system_message.get("content", "")) * 1.2
        return int(total)

    # ---- 管理 ----
    def clear(self, keep_system: bool = True) -> None:
        """清空对话历史"""
        self._messages.clear()
        if not keep_system:
            self._system_message = None

    def _trim(self) -> None:
        """自动裁剪过长的历史（保留最近的）"""
        while len(self._messages) > self._max_messages:
            # 至少保留 system + 2 条对话
            self._messages.pop(0)

        # Token 超限时进一步裁剪
        while self.estimated_tokens > self._max_tokens and len(self._messages) > 4:
            self._messages.pop(0)
            self._messages.pop(0)  # 成对删除

    def __repr__(self) -> str:
        return (f"ConversationContext(messages={len(self._messages)}, "
                f"est_tokens={self.estimated_tokens})")
