from config import SYSTEM_PROMPT
from client import chat
from logger import ChatLogger
from renderer import show,console
from commands import HELP

logger=ChatLogger()
messages=[{"role":"system","content":SYSTEM_PROMPT}]
console.print("[green]AI Chat 已启动[/green]")
while True:
    try:
        q=input("\n你> ").strip()
    except KeyboardInterrupt:
        print("\nBye~")
        break
    if not q: continue
    if q=="/exit": break
    if q=="/help":
        print(HELP);continue
    if q=="/clear":
        messages=[{"role":"system","content":SYSTEM_PROMPT}]
        print("上下文已清空");continue
    if q=="/save":
        print("聊天已自动保存。");continue
    messages.append({"role":"user","content":q});logger.append("User",q)
    stream,obj=chat(messages)
    if stream:
        text=""
        print("AI> ",end="",flush=True)
        for c in obj:
            d=c.choices[0].delta.content
            if d:
                print(d,end="",flush=True);text+=d
        print()
    else:
        text=obj.choices[0].message.content
        show(text)
    messages.append({"role":"assistant","content":text});logger.append("Assistant",text)
