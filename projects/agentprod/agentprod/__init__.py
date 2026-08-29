"""
agentprod — 一个生产级 Agent 框架（基于 OpenAI Responses API）

把我们对话中讨论的所有核心模式落地：
- Agent 循环（配置驱动 + 注册表复用）
- 工具系统（并行批执行、危险工具审批、ask_human 聊天接口化）
- 上下文管理（自动压缩摘要、大结果落盘外置）
- 会话层（持久化、pending 应答路由、模型运行时切换）
- 子 Agent（spawn、深度限制、非交互隔离）
- 聊天接口（REST 长轮询 / CLI 终端两种形态）
"""

__version__ = "1.0.0"
