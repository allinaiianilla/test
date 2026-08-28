"""端到端：真实 openai SDK → HTTP → mock Responses API → 完整 agent 循环。

覆盖 6 个真实链路场景：
1. 纯文本对话（developer 角色映射、消息序列化）
2. 工具调用循环（SQL → 聚合 → 回答）
3. ask_human 挂起 → resume（真实 HTTP 拆成两次调用）
4. 批内混批（普通工具+ask_human）挂起时普通结果已入账
5. 500 错误自动重试后成功
6. 模型切换后用新档案继续
"""
import asyncio, json, sys
sys.path.insert(0, ".")

from agentprod.mock_llm import msg, fcall, start_mock_server
from agentprod.config import ModelProfile
from agentprod.llm import LLMRouter
from agentprod.agent import Agent
from agentprod.tools import PauseForHuman
from agentprod.runtime import Runtime
from agentprod.demo_db import init_demo_db
from agentprod.config import load_agent_configs

init_demo_db()

import glob, os as _os
for _f in glob.glob("data/sessions/*.json"):
    _os.remove(_f)

def build_rt(mock_base):
    """用 mock 服务器替换所有模型档案的 base_url。"""
    rt = Runtime()
    for name, p in rt.model_profiles.items():
        p.base_url_env = None
        object.__setattr__(p, "_mock_base", mock_base)
    # 直接 patch LLMClient 构造
    from agentprod import llm as llm_mod
    orig_init = llm_mod.LLMClient.__init__
    def patched(self, profile, client=None):
        self.profile = profile
        self.adapter = llm_mod.ProtocolAdapter("responses")
        import openai
        self._client = client or openai.OpenAI(
            api_key="mock-key", base_url=profile._mock_base + "/v1")
    llm_mod.LLMClient.__init__ = patched
    return rt

async def main():
    port, server, _ = start_mock_server()
    print(f"== mock server on :{port}")
    rt = build_rt(f"http://127.0.0.1:{port}")

    # ---------- 场景1: 纯文本 ----------
    import urllib.request
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/reset",
        data=json.dumps([{"output": [msg("你好！我是测试助手。")]}]).encode(),
        headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)
    sess = rt.get_or_create_session("e2e_1", "main")
    r = await sess.on_message("你好")
    print(f"1) 纯文本: kind={r.kind} reply={r.text!r} -> {'PASS' if r.kind=='final' and '测试助手' in r.text else 'FAIL'}")

    # ---------- 场景2: SQL 工具循环 ----------
    script = [
        {"output": [fcall("c1", "list_tables", {})]},
        {"output": [fcall("c2", "run_sql",
                          {"sql": "SELECT COUNT(*) n, SUM(amount) total FROM orders WHERE status='paid'"})]},
        {"output": [msg("演示库共有 120 笔订单，其中 paid 订单约 96 笔，总金额约 3.8 万元。")]},
    ]
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/reset",
        data=json.dumps(script).encode(),
        headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)
    sess = rt.get_or_create_session("e2e_2", "analyst")
    r = await sess.on_message("统计 paid 订单数和总金额")
    outs = [m for m in sess.agent.messages if m.get("type")=="function_call_output"]
    ok2 = r.kind=="final" and len(outs)==2
    # 校验 tool result 真实包含 SQL 查询结果
    r1 = json.loads(outs[0]["output"])
    has_tables = isinstance(r1.get("data"), str) and "orders" in r1["data"]
    print(f"2) SQL循环: kind={r.kind} steps={sess.agent.steps_used} tool_outputs={len(outs)} tables_seen={has_tables} -> {'PASS' if ok2 and has_tables else 'FAIL'}")

    # ---------- 场景3: ask_human 挂起→resume ----------
    script = [
        {"output": [fcall("q1", "ask_human", {"question": "查哪个城市的订单？"})]},
        {"output": [msg("北京地区 paid 订单共 18 笔，总金额 7200 元。")]},
    ]
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/reset",
        data=json.dumps(script).encode(),
        headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)
    sess = rt.get_or_create_session("e2e_3", "main")
    r1_ = await sess.on_message("查订单")
    pending_ok = r1_.kind=="ask" and "城市" in r1_.text
    r2_ = await sess.on_message("北京")     # 同一聊天口！
    final_ok = r2_.kind=="final" and "北京" in r2_.text
    # 校验 resume 把用户回答作为 function_call_output 且 call_id 对上
    outs = [m for m in sess.agent.messages if m.get("type")=="function_call_output"]
    resume_ok = outs and outs[-1]["call_id"]=="q1" and "北京" in outs[-1]["output"]
    print(f"3) 挂起问答: first={r1_.kind}({r1_.text!r}) second={r2_.kind} resume_call_id_ok={resume_ok} -> {'PASS' if pending_ok and final_ok and resume_ok else 'FAIL'}")

    # ---------- 场景4: 混批挂起（普通结果先落袋） ----------
    script = [
        {"output": [fcall("t1", "get_time", {}),
                    fcall("q2", "ask_human", {"question": "要什么格式？"}),
                    fcall("c9", "calculator", {"expression": "7*6"})]},
        {"output": [msg("现在是JSON格式，7*6=42。")]},
    ]
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/reset",
        data=json.dumps(script).encode(),
        headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)
    sess = rt.get_or_create_session("e2e_4", "main")
    ra = await sess.on_message("算 7*6")
    mid_outs = [m for m in sess.agent.messages if m.get("type")=="function_call_output"]
    mid_ids = [m["call_id"] for m in mid_outs]
    mixed_ok = ra.kind=="ask" and set(mid_ids)=={"t1","c9"}
    rb = await sess.on_message("JSON格式")
    final_outs = [m for m in sess.agent.messages if m.get("type")=="function_call_output"]
    all_ids = [m["call_id"] for m in final_outs]
    complete_ok = all_ids == ["t1","c9","q2"]
    print(f"4) 混批挂起: mid={mid_ids} final_ids={all_ids} -> {'PASS' if mixed_ok and complete_ok and rb.kind=='final' else 'FAIL'}")

    # 在 reset 前采样请求格式（场景2-4 含工具调用轮次）
    fmt_calls = json.loads(urllib.request.urlopen(
        f"http://127.0.0.1:{port}/calls").read())

    # ---------- 场景5: 500 重试 ----------
    script = [
        {"status": 500},
        {"status": 500},
        {"output": [msg("重试后成功。")]},
    ]
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/reset",
        data=json.dumps(script).encode(),
        headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)
    sess = rt.get_or_create_session("e2e_5", "main")
    r = await sess.on_message("测试重试")
    ok5 = r.kind=="final" and "重试后成功" in r.text
    print(f"5) 500重试: kind={r.kind} -> {'PASS' if ok5 else 'FAIL'}")

    # ---------- 场景6: 模型切换 ----------
    sess = rt.get_or_create_session("e2e_6", "main")
    res = json.loads(sess.agent.switch_model("gpt-4o"))
    req = urllib.request.Request(
        f"http://127.0.0.1:{port}/reset",
        data=json.dumps([{"output": [msg("gpt-4o 档案回复。")]}]).encode(),
        headers={"Content-Type": "application/json"})
    urllib.request.urlopen(req)
    r = await sess.on_message("切换后说话")
    calls = json.loads(urllib.request.urlopen(f"http://127.0.0.1:{port}/calls").read())
    last_model = calls["calls"][-1].get("model")
    ok6 = res["ok"] and r.kind=="final" and last_model=="gpt-4o"
    print(f"6) 模型切换: switched={res['ok']} last_model={last_model} -> {'PASS' if ok6 else 'FAIL'}")

    # ---------- 校验请求格式（真实发给 API 的东西） ----------
    calls = fmt_calls   # 用场景4前采样的数据（含工具调用轮次）
    dev_mapped = any(
        any(i.get("role") == "developer" for i in c["input"])
        for c in calls["calls"])                       # system → developer 映射
    tools_flat = any(
        c.get("tools") and all(t.get("type")=="function" and "name" in t
                               for t in c["tools"])
        for c in calls["calls"])                        # 平铺 schema
    fc_out_fmt = any(
        i.get("type")=="function_call_output" and "call_id" in i
        for c in calls["calls"] for i in c["input"])    # 输出格式
    print(f"7) 请求格式: developer映射={dev_mapped} tools平铺={tools_flat} fc_output格式={fc_out_fmt} -> {'PASS' if dev_mapped and tools_flat and fc_out_fmt else 'FAIL'}")

    print("\n==== E2E 完成 ====")

asyncio.run(main())
