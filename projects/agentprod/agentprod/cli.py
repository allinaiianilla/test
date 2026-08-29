"""CLI 聊天终端：交互层最简实现（验证整套系统）。

- 同步 input() 充当 ask_human 与审批通道
- 危险工具审批在终端里问 y/n
- 演示 pending/resume 的"同一个聊天口"体验
"""
from __future__ import annotations

import asyncio
import json

from .demo_db import init_demo_db
from .runtime import Runtime
from .tools import PauseForHuman, ToolSpec


async def terminal_main(role: str = "main", sid: str = None):
    init_demo_db()
    rt = Runtime()

    # ---- 注入终端版审批与进度 ----
    async def approver(spec: ToolSpec, args: dict) -> bool:
        print(f"\n⚠️  危险操作请求：{spec.name}({json.dumps(args, ensure_ascii=False)})")
        return input("   批准执行？(y/N) > ").strip().lower() == "y"

    async def progress(spec: ToolSpec, args: dict):
        keys = list(args.keys())
        print(f"   ⚙️  调用工具 {spec.name}({', '.join(keys)})...")

    rt.set_interaction(approver=approver, progress=progress)

    sess = rt.get_or_create_session(sid, role)
    print(f"agentprod 终端已启动｜角色={role}｜会话={sess.sid}")
    print("命令：/quit 退出 · /model <profile> 切换模型 · /state 查看状态\n")

    while True:
        try:
            text = input("👤 你 > ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n再见！")
            break
        if not text:
            continue
        if text == "/quit":
            break
        if text.startswith("/model "):
            profile = text.split(None, 1)[1].strip()
            result = sess.agent.switch_model(profile)
            print(f"🤖 切换结果：{result}")
            continue
        if text == "/state":
            print(json.dumps(sess.agent.to_state(), ensure_ascii=False,
                             indent=1)[:2000])
            continue
        if text == "/help":
            print("命令：/quit · /model <profile> · /state")
            continue

        try:
            reply = await sess.on_message(text)
            prefix = "🤖 问你 > " if reply.kind == "ask" else "🤖 > "
            print(prefix + (reply.text or "(无输出)"))
        except PauseForHuman as p:
            print(f"🤖 问你 > {p.question}")


def main():
    asyncio.run(terminal_main())


if __name__ == "__main__":
    main()
