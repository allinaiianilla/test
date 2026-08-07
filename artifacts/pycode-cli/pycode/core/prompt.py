"""
提示词模板 — 构建 system prompt 和工具调用 prompt。
"""

from typing import List

from ..tools import ToolRegistry


def build_system_prompt(
    registry: ToolRegistry,
    workspace: str = ".",
    extra_context: str = ""
) -> str:
    """
    构建 Agent 的 system prompt。

    包含：
    1. 角色定义
    2. 工具列表
    3. 工作空间信息
    4. 行为约束
    """
    prompt = f"""你是 PyCode，一个 Python 编程助手 Agent。
你运行在命令行环境，帮助用户编写代码、分析项目、解决问题。

## 工作目录
{workspace}

{extra_context}

## 你的能力
你拥有以下工具，可以在需要时调用它们来获取信息或执行操作：
{registry.tools_prompt()}

## 工具调用格式
当需要使用工具时，用以下 JSON 格式回复：

```tool_call
{{
  "name": "工具名",
  "arguments": {{"参数": "值"}}
}}
```

如果需要调用多个工具，可以输出多个 ```tool_call 块。

## 行为准则
1. **先看再写**：写代码前先用 read_file 或 list_dir 了解项目结构
2. **简洁回复**：代码要带注释，解释要到位但别啰嗦
3. **安全第一**：涉及删除、重命名的操作要提醒用户确认
4. **中文回复**：解释用中文，代码和变量名用英文
5. **鼓励实践**：给出可以直接运行的代码

现在，开始帮助用户吧！"""
    return prompt


def format_user_message(query: str) -> str:
    """格式化用户消息"""
    return query


def format_tool_result(tool_name: str, result: str) -> str:
    """格式化工具执行结果"""
    # 截断过长结果
    if len(result) > 3000:
        result = result[:3000] + f"\n... (已截断，共 {len(result)} 字符)"
    return f"[工具 {tool_name} 返回]:\n{result}"


def format_conversation_context(
    messages: list,
    recent_n: int = 10
) -> str:
    """
    格式化最近的对话上下文。

    Args:
        messages: [{"role": str, "content": str}, ...]
        recent_n: 保留最近 N 条消息
    """
    recent = messages[-recent_n:] if len(messages) > recent_n else messages
    formatted = []
    for msg in recent:
        role = msg.get("role", "unknown")
        content = msg.get("content", "")[:500]
        formatted.append(f"[{role}]: {content}")
    return "\n".join(formatted)
