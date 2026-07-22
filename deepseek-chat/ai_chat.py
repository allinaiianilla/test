#!/usr/bin/env python3
"""
AI 大模型终端对话程序
- 支持连续多轮对话，保持上下文
- 终端中使用 Rich 库实现 Markdown/代码语法高亮
- 每次对话自动追加写入对话记录文件
- 支持 /exit 退出，/clear 清空上下文，/save 手动保存

使用方式：
    python ai_chat.py
    python ai_chat.py --model gpt-4
"""

import os
import sys
import json
import argparse
from datetime import datetime
from pathlib import Path

import requests
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.rule import Rule
from rich.text import Text

# ============================================================
# 配置区域 —— 根据你的 API 修改以下参数
# ============================================================
CONFIG = {
    "api_base": os.environ.get("AI_API_BASE", "https://api.openai.com/v1"),
    "api_key": os.environ.get("AI_API_KEY", "sk-your-api-key-here"),
    "model": os.environ.get("AI_MODEL", "gpt-3.5-turbo"),
    "max_tokens": 4096,
    "temperature": 0.7,
    "system_prompt": "你是一个有帮助的AI助手。如果回答中包含代码，请使用Markdown代码块格式。",
}

# 对话日志保存目录
LOG_DIR = Path.home() / ".ai_chat_logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# ============================================================
# 核心类
# ============================================================

class AIChat:
    """AI 对话客户端"""

    def __init__(self, config: dict):
        self.config = config
        self.messages: list[dict] = []
        self.console = Console()
        self._init_session()

    def _init_session(self):
        """初始化会话，设置 system prompt"""
        self.messages = [
            {"role": "system", "content": self.config["system_prompt"]}
        ]
        # 生成本次对话的日志文件
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.log_file = LOG_DIR / f"chat_{timestamp}.jsonl"

    def _call_api(self) -> str | None:
        """调用大模型 API，返回模型回复文本"""
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.config['api_key']}",
        }
        payload = {
            "model": self.config["model"],
            "messages": self.messages,
            "max_tokens": self.config["max_tokens"],
            "temperature": self.config["temperature"],
        }

        url = f"{self.config['api_base'].rstrip('/')}/chat/completions"

        try:
            resp = requests.post(url, headers=headers, json=payload, timeout=120)
            resp.raise_for_status()
            data = resp.json()
            return data["choices"][0]["message"]["content"]
        except requests.exceptions.Timeout:
            self.console.print("[red]❌ 请求超时，请检查网络或稍后重试[/red]")
            return None
        except requests.exceptions.HTTPError as e:
            self.console.print(f"[red]❌ HTTP 错误: {e}[/red]")
            if resp.text:
                self.console.print(f"[dim]{resp.text[:500]}[/dim]")
            return None
        except requests.exceptions.ConnectionError:
            self.console.print("[red]❌ 连接失败，请检查 API_BASE 地址和网络[/red]")
            return None
        except (KeyError, IndexError, json.JSONDecodeError) as e:
            self.console.print(f"[red]❌ 解析响应失败: {e}[/red]")
            self.console.print(f"[dim]原始响应: {resp.text[:500]}[/dim]")
            return None

    def _append_to_log(self, role: str, content: str):
        """将一条消息追加写入日志文件（JSONL 格式，每条一行）"""
        record = {
            "timestamp": datetime.now().isoformat(),
            "role": role,
            "content": content,
        }
        with open(self.log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def chat(self):
        """主对话循环"""
        self.console.clear()
        self.console.print(
            Panel.fit(
                f"[bold cyan]🤖 AI 对话助手[/bold cyan]\n"
                f"模型: {self.config['model']}\n"
                f"日志: {self.log_file}\n\n"
                f"命令: [yellow]/exit[/yellow] 退出  "
                f"[yellow]/clear[/yellow] 清空上下文  "
                f"[yellow]/save[/yellow] 查看日志路径",
                border_style="cyan",
            )
        )

        while True:
            try:
                user_input = Prompt.ask("\n[bold green]你[/bold green]")
            except (KeyboardInterrupt, EOFError):
                self.console.print("\n[yellow]👋 再见！[/yellow]")
                break

            user_input = user_input.strip()
            if not user_input:
                continue

            # ---- 处理内置命令 ----
            if user_input.lower() == "/exit":
                self.console.print("[yellow]👋 再见！[/yellow]")
                break
            if user_input.lower() == "/clear":
                self._init_session()
                self.console.print("[green]✅ 上下文已清空，开始新对话[/green]")
                continue
            if user_input.lower() == "/save":
                self.console.print(f"[dim]📁 对话日志: {self.log_file}[/dim]")
                continue

            # ---- 正常对话 ----
            self.messages.append({"role": "user", "content": user_input})
            self._append_to_log("user", user_input)

            # 显示等待状态
            with self.console.status("[cyan]思考中...[/cyan]", spinner="dots"):
                reply = self._call_api()

            if reply is None:
                # API 调用失败，移除刚才添加的 user 消息避免污染上下文
                self.messages.pop()
                continue

            self.messages.append({"role": "assistant", "content": reply})
            self._append_to_log("assistant", reply)

            # 渲染回复
            self.console.print()
            self.console.print(
                Panel(
                    Markdown(reply, code_theme="monokai"),
                    title="[bold cyan]AI[/bold cyan]",
                    border_style="cyan",
                )
            )


# ============================================================
# 入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="AI 大模型终端对话程序")
    parser.add_argument("--model", "-m", help="指定模型名称，覆盖配置")
    parser.add_argument("--api-key", "-k", help="API Key，覆盖配置")
    parser.add_argument("--api-base", "-b", help="API Base URL，覆盖配置")
    args = parser.parse_args()

    config = CONFIG.copy()
    if args.model:
        config["model"] = args.model
    if args.api_key:
        config["api_key"] = args.api_key
    if args.api_base:
        config["API_URL"] = args.api_base

    # 检查 API Key
    if config["api_key"] == "sk-your-api-key-here":
        print("⚠️  请先设置 API Key！")
        print("   方式1: export AI_API_KEY='your-key'")
        print("   方式2: python ai_chat.py -k 'your-key'")
        print("   方式3: 直接修改脚本中的 CONFIG 字典")
        sys.exit(1)

    chat = AIChat(config)
    chat.chat()


if __name__ == "__main__":
    main()