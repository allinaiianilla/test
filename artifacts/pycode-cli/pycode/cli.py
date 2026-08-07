#!/usr/bin/env python3
"""
PyCode CLI — 命令行入口。

用法:
    # 单次问答
    pycode "给这个项目写单元测试"

    # 交互式 REPL
    pycode repl

    # 初始化配置
    pycode init

    # 查看版本
    pycode --version
"""

import sys
import os
from pathlib import Path

# 确保能导入 pycode 包
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from pycode import __version__
from pycode.llm import OpenAICompatibleLLM
from pycode.tools import ToolRegistry, register_builtin_tools
from pycode.core import Agent
from pycode.config import Config


# ============================================================
# 彩色输出（跨平台）
# ============================================================
def supports_color() -> bool:
    """检测终端是否支持颜色"""
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    return hasattr(sys.stdout, "isatty") and sys.stdout.isatty()


class Colors:
    """ANSI 颜色代码"""
    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    CYAN = "\033[36m"


def colorize(text: str, color: str) -> str:
    """给文本加颜色（如果不支持颜色则原样返回）"""
    if not supports_color():
        return text
    return f"{color}{text}{Colors.RESET}"


# ============================================================
# 交互式 REPL
# ============================================================
def repl_mode(config: Config) -> None:
    """
    进入交互式 REPL 模式。

    特殊命令:
    - /help    — 帮助
    - /reset   — 重置上下文
    - /tools   — 列出可用工具
    - /exit    — 退出
    """
    print(colorize(f"\n🦞 PyCode CLI v{__version__} — 输入 /help 查看帮助，/exit 退出\n",
                   Colors.CYAN))

    # 初始化
    llm = _create_llm(config)
    agent = Agent(llm, config)

    print(colorize(f"模型: {llm.model_name}", Colors.DIM))
    print(colorize(f"工具: {len(agent._registry)} 个已注册\n", Colors.DIM))

    while True:
        try:
            user_input = input(colorize("你> ", Colors.GREEN)).strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 再见!")
            break

        if not user_input:
            continue

        # 处理特殊命令
        if user_input.startswith("/"):
            cmd = user_input[1:].lower().split()
            if cmd[0] == "exit" or cmd[0] == "quit":
                print("👋 再见!")
                break
            elif cmd[0] == "help":
                print("""
📋 可用命令:
  /help     — 显示帮助
  /reset    — 重置对话上下文
  /tools    — 列出可用工具
  /exit     — 退出

💡 你也可以直接输入任何编程问题！
""")
            elif cmd[0] == "reset":
                agent.reset()
                print(colorize("✅ 上下文已重置", Colors.GREEN))
            elif cmd[0] == "tools":
                print("\n🔧 可用工具:")
                for tool in agent._registry.list():
                    danger = " ⚠️危险" if tool.dangerous else ""
                    print(f"  {tool.name}: {tool.description}{danger}")
                print()
            else:
                print(colorize(f"未知命令: /{cmd[0]}，输入 /help 查看帮助",
                              Colors.YELLOW))
            continue

        # 正常对话
        print(colorize("PyCode> ", Colors.BLUE), end="", flush=True)
        try:
            for chunk in agent.run_stream(user_input):
                print(chunk, end="", flush=True)
            print()
        except Exception as e:
            print(colorize(f"\n❌ 错误: {e}", Colors.RED))


# ============================================================
# 单次模式
# ============================================================
def oneshot_mode(query: str, config: Config) -> None:
    """单次问答模式"""
    llm = _create_llm(config)
    agent = Agent(llm, config)

    try:
        for chunk in agent.run_stream(query):
            print(chunk, end="", flush=True)
        print()
    except Exception as e:
        print(colorize(f"\n❌ 错误: {e}", Colors.RED))
        sys.exit(1)


# ============================================================
# 初始化配置
# ============================================================
def init_config() -> None:
    """初始化配置文件"""
    config_dir = Path.home() / ".pycode"
    config_dir.mkdir(exist_ok=True)
    config_path = config_dir / "config.json"

    if config_path.exists():
        overwrite = input(f"{config_path} 已存在，覆盖? (y/n) ")
        if overwrite.lower() != "y":
            return

    print("🔧 配置 PyCode CLI\n")

    api_key = input("API Key (留空则从环境变量 PYCODE_API_KEY 读取): ").strip()
    base_url = input(f"API Base URL [https://api.openai.com/v1]: ").strip()
    model = input(f"模型 [gpt-4o-mini]: ").strip()

    config = {
        "llm": {
            "provider": "openai_compat",
            "base_url": base_url or "https://api.openai.com/v1",
            "model": model or "gpt-4o-mini",
            "max_tokens": 4096,
            "temperature": 0.7,
        },
        "tools": {
            "allow_shell": False,
            "allow_write": True,
            "workspace": ".",
        },
        "ui": {
            "stream": True,
            "color": True,
        },
        "agent": {
            "max_turns": 10,
            "context_lines": 50,
        }
    }

    import json
    with open(config_path, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\n✅ 配置已保存: {config_path}")

    # 提示设置环境变量
    if api_key:
        print(f"\n⚠️ 建议设置环境变量而非写入配置文件:")
        print(colorize(f'  export PYCODE_API_KEY="{api_key}"', Colors.YELLOW))
        print(f"\n或添加到 ~/.bashrc / ~/.zshrc")


# ============================================================
# LLM 工厂
# ============================================================
def _create_llm(config: Config) -> OpenAICompatibleLLM:
    """根据配置创建 LLM 实例"""
    api_key = config.llm.api_key or os.environ.get("PYCODE_API_KEY", "")
    if not api_key:
        print(colorize(
            "❌ 未设置 API Key。请通过以下方式之一设置:\n"
            "  1. export PYCODE_API_KEY=\"your-key\"\n"
            "  2. pycode init 初始化配置",
            Colors.RED
        ))
        sys.exit(1)

    return OpenAICompatibleLLM(
        api_key=api_key,
        base_url=config.llm.base_url,
        model=config.llm.model,
        max_tokens=config.llm.max_tokens,
        temperature=config.llm.temperature,
    )


# ============================================================
# 主入口
# ============================================================
def main():
    """CLI 主入口"""
    args = sys.argv[1:]

    # --version
    if "--version" in args or "-V" in args:
        print(f"PyCode CLI v{__version__}")
        sys.exit(0)

    # 加载配置
    config = Config.load()

    # pycode init
    if args and args[0] == "init":
        init_config()
        sys.exit(0)

    # pycode repl
    if args and args[0] == "repl":
        repl_mode(config)
        sys.exit(0)

    # 无参数 → 帮助
    if not args:
        print(f"🦞 PyCode CLI v{__version__}")
        print()
        print("用法:")
        print('  pycode "你的问题"     — 单次问答')
        print("  pycode repl          — 交互式对话")
        print("  pycode init          — 初始化配置")
        print("  pycode --version     — 查看版本")
        print()
        print("示例:")
        print('  pycode "帮我写一个快速排序"')
        print('  pycode "这个项目里有哪些函数"')
        sys.exit(0)

    # 单次模式
    query = " ".join(args)
    oneshot_mode(query, config)


if __name__ == "__main__":
    main()
