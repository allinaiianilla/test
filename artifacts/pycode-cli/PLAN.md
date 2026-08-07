# PyCode CLI — Python 智能编程助手

> 一个轻量级的 Python Agent / CLI 工具，让 AI 帮你写代码、读项目、分析错误。
> 设计哲学：**简单、可扩展、本地运行、零外部依赖**。

---

## 一、项目定位

| 维度 | 说明 |
|------|------|
| **目标用户** | Python 开发者、学习者 |
| **核心能力** | LLM 驱动的代码生成、项目问答、错误分析 |
| **交互方式** | CLI 命令行 + 交互式 REPL |
| **技术栈** | Python 3.10+ 标准库 + 可插拔 LLM 后端 |
| **设计原则** | 单一职责、模块化、易扩展、文档齐全 |

---

## 二、架构设计

```
pycode-cli/
├── pycode/
│   ├── __init__.py
│   ├── cli.py              # 命令行入口 + REPL 循环
│   ├── llm/
│   │   ├── __init__.py
│   │   ├── base.py         # LLM 抽象基类 (统一接口)
│   │   └── openai_compat.py # OpenAI 兼容 API (可接任何兼容服务)
│   ├── tools/
│   │   ├── __init__.py
│   │   ├── registry.py     # 工具注册中心
│   │   ├── file_ops.py     # 文件读写工具
│   │   ├── shell_ops.py    # Shell 命令执行
│   │   └── code_ops.py     # Python 代码执行与静态分析
│   ├── core/
│   │   ├── __init__.py
│   │   ├── agent.py        # Agent 主循环 (ReAct 模式)
│   │   ├── context.py      # 对话上下文管理
│   │   └── prompt.py       # 提示词模板
│   └── config/
│       ├── __init__.py
│       └── settings.py     # 配置管理 (环境变量 + 配置文件)
├── tests/                  # 单元测试
├── docs/                   # 详细文档
├── setup.py
├── requirements.txt
└── README.md
```

---

## 三、核心模块设计

### 3.1 LLM 抽象层 (`llm/`)

```python
class BaseLLM(ABC):
    """LLM 统一接口"""
    @abstractmethod
    def chat(self, messages: list[dict]) -> str: ...
    
    @abstractmethod
    def chat_stream(self, messages: list[dict]) -> Iterator[str]: ...

class OpenAICompatibleLLM(BaseLLM):
    """OpenAI / 智谱 / DeepSeek / 本地 Ollama 等兼容"""
```

**关键设计：** 一个抽象类 + 一个实现，覆盖 90% API 提供商（都兼容 OpenAI 格式）。

### 3.2 工具系统 (`tools/`)

```python
@dataclass
class Tool:
    name: str
    description: str
    parameters: dict       # JSON Schema 格式
    function: Callable     # 实际执行函数

class ToolRegistry:
    """工具注册中心：注册 → 生成 prompt → 执行调度"""
```

**内置工具：**

| 工具 | 功能 | 权限 |
|------|------|------|
| `read_file` | 读取文件内容 | 安全 |
| `write_file` | 写入文件 | 需确认 |
| `list_dir` | 列出目录结构 | 安全 |
| `run_shell` | 执行 Shell 命令 | 需确认 |
| `search_code` | grep 搜索代码 | 安全 |
| `python_repl` | 执行 Python 片段 | 沙箱模式 |

### 3.3 Agent 引擎 (`core/agent.py`)

**采用 ReAct (Reasoning + Acting) 模式：**

```
用户: "帮我写一个冒泡排序"
  ↓
Agent 思考 → 我该调用什么工具
  ↓ (可选)
Agent 动作 → read_file/ls/grep 了解上下文
  ↓
Agent 思考 → 现在我可以生成代码了
  ↓
Agent 动作 → write_file 写入代码
  ↓
返回给用户完整回答
```

### 3.4 CLI 入口 (`cli.py`)

两种模式：
- **单次模式**：`pycode "给这个项目写单元测试"`
- **交互模式**：`pycode repl` → 进入对话式 REPL

---

## 四、技术亮点

1. **零强制依赖**：标准库实现核心，LLM 调用用 `urllib`
2. **可插拔 LLM**：换 API Key 就能换模型
3. **工具即函数**：加新工具 = 写一个普通 Python 函数 + `@register_tool` 装饰器
4. **上下文感知**：自动收集项目文件树、最近修改等上下文
5. **沙箱执行**：Python REPL 限制危险操作

---

## 五、开发路线图

| 阶段 | 内容 | 预计时间 |
|------|------|----------|
| **Phase 1** | 项目骨架 + LLM 抽象层 + 基础 CLI | 立即开始 |
| **Phase 2** | 工具注册系统 + 3 个基础工具 | 紧随其后 |
| **Phase 3** | Agent ReAct 主循环 | 核心逻辑 |
| **Phase 4** | 上下文管理 + 提示词优化 | 体验提升 |
| **Phase 5** | 测试 + 文档 + 打包 | 收尾 |

---

## 六、配置示例 (`~/.pycode/config.yaml`)

```yaml
llm:
  provider: openai_compat
  api_key: ${PYCODE_API_KEY}
  base_url: https://api.openai.com/v1
  model: gpt-4o-mini
  max_tokens: 4096
  temperature: 0.7

tools:
  allow_shell: false       # 安全：默认禁用 shell
  allow_write: true
  workspace: ./            # 默认当前目录

ui:
  stream: true             # 流式输出
  color: true              # 彩色输出
```

---

*计划书 v1.0 — by CloudClaw 🦞*
