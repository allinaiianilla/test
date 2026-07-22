# 🦞 PyCode CLI — Python 智能编程助手

一个轻量级的 Python Agent CLI 工具，通过 LLM 帮你写代码、读项目、分析错误。

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green)](LICENSE)

## ✨ 特性

- **零强制依赖**：核心用 Python 标准库实现
- **可插拔 LLM**：OpenAI / 智谱 / DeepSeek / Ollama 随意切换
- **ReAct Agent**：自主思考 → 调用工具 → 观察结果 → 迭代求解
- **内置工具**：读文件、写文件、列目录、搜索代码、执行脚本
- **交互式 REPL**：像聊天一样编程
- **安全第一**：危险操作需确认，默认禁用 Shell 执行

## 🚀 快速开始

### 安装

```bash
pip install -e .
# 或者直接运行
python -m pycode.cli
```

### 设置 API Key

```bash
# 方式一：环境变量（推荐）
export PYCODE_API_KEY="your-api-key"

# 方式二：配置文件
pycode init
```

### 使用

```bash
# 单次问答
pycode "帮我写一个冒泡排序，带详细注释"

# 交互式对话
pycode repl

# 分析项目
pycode "这个项目有哪些 Python 文件？分别做什么用的？"

# 调试代码
pycode "我的 app.py 第 42 行报 IndexError，可能是什么原因？"
```

## 🔌 支持的 LLM 提供商

| 提供商 | 配置 |
|--------|------|
| **OpenAI** | `base_url: https://api.openai.com/v1` |
| **智谱 GLM** | `base_url: https://open.bigmodel.cn/api/paas/v4` |
| **DeepSeek** | `base_url: https://api.deepseek.com/v1` |
| **Ollama 本地** | `base_url: http://localhost:11434/v1` |

## 📦 项目结构

```
pycode-cli/
├── pycode/                 # 主包
│   ├── cli.py              # 命令行入口 + REPL
│   ├── llm/                # LLM 抽象层
│   │   ├── base.py         # 抽象基类
│   │   └── openai_compat.py # OpenAI 兼容实现
│   ├── tools/              # 工具系统
│   │   ├── registry.py     # 工具注册中心
│   │   └── file_ops.py     # 内置工具集
│   ├── core/               # Agent 引擎
│   │   ├── agent.py        # ReAct Agent 主循环
│   │   ├── context.py      # 对话上下文
│   │   └── prompt.py       # 提示词模板
│   └── config/             # 配置管理
│       └── settings.py     # 配置加载/合并
├── tests/                  # 单元测试
├── PLAN.md                 # 架构设计文档
├── setup.py                # 安装脚本
└── README.md               # 本文件
```

## 🎯 使用示例

### 示例 1：写代码

```
你> 写一个斐波那契数列生成器，用 yield
PyCode> 这是使用生成器实现的斐波那契数列：

\`\`\`python
def fibonacci(n):
    """生成前 n 个斐波那契数"""
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

# 使用
for num in fibonacci(10):
    print(num, end=" ")  # 0 1 1 2 3 5 8 13 21 34
\`\`\`

特点：内存高效，按需生成，不会一次性创建整个列表。
```

### 示例 2：分析项目

```
你> 看看项目里有哪些模块，各负责什么
PyCode> 🔧 调用 2 个工具...
  - list_dir(".")
  - read_file("pycode/__init__.py")

📊 项目分析：
- cli.py: 命令行入口，处理参数和交互
- llm/: LLM 封装层，支持多种 API
- tools/: 工具系统，文件/Shell/代码操作
- core/: Agent 引擎 + 对话管理
- config/: 配置加载和环境变量处理
```

### 示例 3：调试

```
你> test_api.py 报 401 Unauthorized，帮我看看
PyCode> 🔧 调用 read_file("test_api.py")
🔧 调用 search_code("401")

看了代码和错误信息，问题是第 15 行 headers 没有传 API Key。

修复方案：
在 headers 中加一行：
\`\`\`python
headers["Authorization"] = f"Bearer {os.environ['API_KEY']}"
\`\`\`
```

## 🛡️ 安全策略

| 操作 | 默认状态 | 说明 |
|------|---------|------|
| 读文件 | ✅ 允许 | 安全的只读操作 |
| 列目录 | ✅ 允许 | 查看项目结构 |
| 搜索代码 | ✅ 允许 | grep 式搜索 |
| 写文件 | ⚠️ 需确认 | 可能覆盖文件 |
| 执行 Shell | ❌ 默认禁用 | 高风险操作 |
| 执行 Python | ❌ 默认禁用 | 受沙箱限制 |

## 📄 License

MIT — by CloudClaw 🦞
