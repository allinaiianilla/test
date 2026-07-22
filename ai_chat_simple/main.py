from pathlib import Path
from datetime import datetime
import httpx
from openai import OpenAI
from rich.console import Console
from rich.markdown import Markdown
from config import *

console=Console()
client=OpenAI(api_key=API_KEY,base_url=BASE_URL,http_client=httpx.Client(trust_env=False))
history=Path("history");history.mkdir(exist_ok=True)
log=history/f"{datetime.now():%Y%m%d_%H%M%S}.md"
msgs=[{"role":"system","content":SYSTEM_PROMPT}]
log.write_text("# Chat\n\n",encoding="utf8")
def save(r,t):
    with log.open("a",encoding="utf8") as f:f.write(f"## {r}\n\n{t}\n\n---\n\n")
while True:
    try:q=input("你> ").strip()
    except KeyboardInterrupt:break
    if not q:continue
    if q=="/exit":break
    if q=="/clear":msgs=[{"role":"system","content":SYSTEM_PROMPT}];print("已清空");continue
    if q=="/help":print("/help /clear /exit");continue
    msgs.append({"role":"user","content":q});save("User",q);ans=""
    try:
        comp=client.chat.completions.create(model=MODEL,messages=msgs,stream=True)
        print("AI> ",end="")
        for chunk in comp:
            if not getattr(chunk,"choices",None):continue
            c=chunk.choices[0].delta.content
            if c:print(c,end="",flush=True);ans+=c
        print()
    except Exception:
        r=client.chat.completions.create(model=MODEL,messages=msgs)
        ans=r.choices[0].message.content or ""
        console.print(Markdown(ans))
    msgs.append({"role":"assistant","content":str(ans)});save("Assistant",ans)
print("Bye")
