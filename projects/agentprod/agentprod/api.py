"""聊天 REST API（FastAPI）：生产可用的交互层。

接口设计（对应讨论的"交互程序"层）：
- POST /chat                 发消息（自动按 pending 路由 run/resume）
- GET  /sessions             会话列表
- POST /sessions             新建会话
- DELETE /sessions/{sid}     删除会话
- GET  /sessions/{sid}/state 查看会话状态（含挂起问题）
- POST /sessions/{sid}/model 切换模型档案（外部切换接口）
- GET  /models               可用模型列表
- GET  /health               健康检查

审批与进度通过 WebSocket/SSE 可扩展；当前默认实现：
- 危险工具默认拒绝（生产可换成审批队列 + 通知）
- 工具进度进事件队列，随最终回复附带
"""
from __future__ import annotations

import asyncio
import json
import time
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from .runtime import Runtime, SessionReply


# 请求模型必须模块级定义：
# (from __future__ import annotations 会把注解字符串化，
#  函数内定义的类无法被 FastAPI 解析，会被误判为 query 参数)

class ChatIn(BaseModel):
    sid: Optional[str] = None
    text: str
    role: str = "main"


class NewSessionIn(BaseModel):
    role: str = "main"


class ModelIn(BaseModel):
    profile: str


def create_app(runtime: Runtime = None) -> FastAPI:
    app = FastAPI(title="agentprod Chat API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware, allow_origins=["*"], allow_methods=["*"],
        allow_headers=["*"])

    rt = runtime or Runtime()
    app.state.rt = rt

    # ---------------- 路由 ----------------

    @app.post("/chat")
    async def chat(body: ChatIn):
        if not body.text or not body.text.strip():
            raise HTTPException(400, "text 不能为空")
        sess = rt.get_or_create_session(body.sid, body.role)
        started = time.time()
        reply: SessionReply = await sess.on_message(body.text.strip())
        return {**reply.to_dict(),
                "elapsed_ms": int((time.time() - started) * 1000)}

    @app.get("/sessions")
    async def sessions():
        return {"sessions": rt.list_sessions()}

    @app.post("/sessions")
    async def new_session(body: NewSessionIn = None):
        role = body.role if body is not None else "main"
        if role not in rt.agent_configs:
            raise HTTPException(404, f"未知角色: {role}")
        sess = rt.get_or_create_session(None, role)
        return {"sid": sess.sid, "role": role,
                "model": sess.agent.model_profile}

    @app.delete("/sessions/{sid}")
    async def delete_session(sid: str):
        rt.close_session(sid)
        return {"ok": True}

    @app.get("/sessions/{sid}/state")
    async def session_state(sid: str):
        sess = rt.get_or_create_session(sid)
        st = sess.agent.to_state()
        return {
            "sid": sid,
            "role": sess.agent.cfg.name,
            "model": sess.agent.model_profile,
            "steps_used": sess.agent.steps_used,
            "pending": (None if not sess.agent.pending else {
                "question": sess.agent.pending.question,
                "created_at": sess.agent.pending.created_at,
            }),
            "message_count": len(st["messages"]),
        }

    @app.post("/sessions/{sid}/model")
    async def switch_model(sid: str, body: ModelIn):
        try:
            result = rt.switch_session_model(sid, body.profile)
        except KeyError as e:
            raise HTTPException(404, str(e))
        return result

    @app.get("/models")
    async def models():
        items = []
        for n, p in rt.model_profiles.items():
            items.append({"profile": n, "model": p.model,
                          "summary": p.is_summary_model,
                          "context_window": p.context_window,
                          "default": n == rt.router.default_name})
        return {"models": items, "default": rt.router.default_name,
                "summary_model": rt.router.summary_name}

    @app.get("/health")
    async def health():
        return {"ok": True, "ts": time.time(),
                "active_sessions": len(rt.sessions)}

    return app


def main():  # pragma: no cover
    """命令行启动：uvicorn agentprod.api:create_app"""
    import uvicorn
    uvicorn.run("agentprod.api:create_app", factory=True,
                host="0.0.0.0", port=8901, reload=False)


if __name__ == "__main__":  # pragma: no cover
    main()
