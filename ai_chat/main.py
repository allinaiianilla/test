from config import SYSTEM_PROMPT
from client import chat
from logger import ChatLogger
from renderer import show, console
from commands import HELP

logger = ChatLogger()

messages = [
    {
        "role": "system",
        "content": SYSTEM_PROMPT
    }
]

console.print("[bold green]AI Chat 已启动[/bold green]")
console.print("[cyan]输入 /help 查看帮助[/cyan]")

while True:

    try:
        question = input("\n你 > ").strip()

    except KeyboardInterrupt:
        print("\n\nBye~")
        break

    if not question:
        continue

    # -----------------------
    # 命令
    # -----------------------

    if question == "/exit":
        break

    if question == "/help":
        print(HELP)
        continue

    if question == "/clear":
        messages = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT
            }
        ]
        console.print("[yellow]上下文已清空[/yellow]")
        continue

    if question == "/save":
        console.print("[green]聊天记录始终自动保存。[/green]")
        continue

    # -----------------------
    # 用户消息
    # -----------------------

    messages.append(
        {
            "role": "user",
            "content": question
        }
    )

    logger.append("User", question)

    # -----------------------
    # AI
    # -----------------------

    answer, stream = chat(messages)

    if not stream:
        show(answer)

    messages.append(
        {
            "role": "assistant",
            "content": answer
        }
    )

    logger.append("Assistant", answer)

print("\n聊天结束。")