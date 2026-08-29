"""本地 Mock LLM 服务器：OpenAI Responses API 兼容，用于"模拟真实 API 调用"。

- POST /v1/responses  按"脚本"回放模型行为（消息 / function_call / 500 错误）
- POST /reset         注入新脚本并清零调用记录
- GET  /calls         查看收到的全部请求（校验 input 格式、tools schema）
- GET  /health        健康检查

真实链路验证点：openai SDK → base_url 路由 → developer 角色映射 →
平铺 tools schema → function_call 解析 → 工具结果回传 → 429/5xx 退避重试。
"""
from __future__ import annotations

import threading
import time
from typing import Optional

from fastapi import FastAPI, Request, Response
from fastapi.responses import JSONResponse

LOCK = threading.Lock()
STATE = {"calls": [], "n": 0, "script": []}


def msg(text: str) -> dict:
    """一条 assistant 消息输出块。"""
    return {"type": "message", "id": "msg_m", "role": "assistant",
            "status": "completed",
            "content": [{"type": "output_text", "text": text, "annotations": []}]}


def fcall(call_id: str, name: str, args: dict) -> dict:
    """一个 function_call 输出块。"""
    return {"type": "function_call", "id": f"fc_{call_id}", "call_id": call_id,
            "name": name, "arguments": json.dumps(args, ensure_ascii=False),
            "status": "completed"}


def json_dumps_default(o):
    import json as _j
    return _j.dumps(o, ensure_ascii=False)


import json  # noqa: E402


def create_mock_app() -> FastAPI:
    app = FastAPI(title="Mock Responses API")

    @app.get("/health")
    async def health():
        return {"ok": True}

    @app.post("/reset")
    async def reset(request: Request):
        script = await request.json()
        with LOCK:
            STATE["calls"] = []
            STATE["n"] = 0
            STATE["script"] = script
        return {"ok": True, "script_len": len(script)}

    @app.get("/calls")
    async def calls():
        with LOCK:
            return {"count": len(STATE["calls"]), "calls": STATE["calls"]}

    @app.post("/v1/responses")
    async def responses(request: Request):
        params = await request.json()
        with LOCK:
            idx = STATE["n"]
            STATE["n"] += 1
            STATE["calls"].append(params)
            entry = STATE["script"][min(idx, len(STATE["script"]) - 1)] \
                if STATE["script"] else {"output": [msg("(empty script)")]}

        # 可注入错误：{"status": 500} 或 {"status": 429}
        status = entry.get("status")
        if status:
            return JSONResponse(status_code=status,
                                content={"error": {"message": f"mock {status}"}})

        return {
            "id": f"resp_{idx}", "object": "response",
            "created_at": int(time.time()), "status": "completed",
            "model": params.get("model", "mock"),
            "output": entry.get("output", []),
            "parallel_tool_calls": True, "tool_choice": "auto",
            "tools": params.get("tools", []),
            "usage": {"input_tokens": 120, "output_tokens": 60,
                      "total_tokens": 180},
        }

    return app


def start_mock_server(host="127.0.0.1", port: Optional[int] = None):
    """在后台线程起 mock 服务器，返回 (port, server, thread)。"""
    import socket
    import urllib.request

    import uvicorn

    if port is None:
        s = socket.socket()
        s.bind((host, 0))
        port = s.getsockname()[1]
        s.close()

    server = uvicorn.Server(uvicorn.Config(
        create_mock_app(), host=host, port=port, log_level="error"))
    t = threading.Thread(target=server.run, daemon=True)
    t.start()
    base = f"http://{host}:{port}"
    for _ in range(100):
        try:
            urllib.request.urlopen(f"{base}/health", timeout=1)
            return port, server, t
        except Exception:  # noqa: BLE001
            time.sleep(0.1)
    raise RuntimeError("mock server 启动失败")


if __name__ == "__main__":  # pragma: no cover
    import uvicorn
    uvicorn.run(create_mock_app(), host="127.0.0.1", port=8931)
