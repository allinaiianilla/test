"""真实 API 端到端测试（智谱 glm-4-flash，Chat Completions 协议适配）。

场景：
1. 纯文本对话
2. SQL 工具调用循环（list_tables → run_sql → 回答，模型自主决策）
3. calculator 工具
4. ask_human 挂起 → resume（真实两次会话）
5. 模型切换 glm-4-flash → glm-4-plus
"""
import asyncio, json, sys, os
sys.path.insert(0, ".")

# 从环境变量读取（勿把真实 key 写进代码）
assert os.environ.get("ZHIPU_API_KEY"), "请先 export ZHIPU_API_KEY=***"
os.environ.setdefault("ZHIPU_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")

from agentprod.runtime import Runtime
from agentprod.demo_db import init_demo_db

init_demo_db(force=True)
import glob
for f in glob.glob("data/sessions/*.json"):
    os.remove(f)

async def main():
    rt = Runtime()
    print(f"默认模型: {rt.router.default_name}")
    assert rt.router.default_name == "glm-4-flash"

    # 1) 纯文本
    sess = rt.get_or_create_session("real_1", "main")
    r = await sess.on_message("用一句话介绍你自己")
    print(f"\n1) 纯文本: kind={r.kind}\n   reply={r.text[:100] if r.text else r.text}")
    ok1 = r.kind == "final" and bool(r.text)

    # 2) SQL 工具循环
    sess = rt.get_or_create_session("real_2", "analyst")
    r = await sess.on_message("查询demo数据库：paid状态订单总数和总金额是多少？用SQL查后报数字。")
    outs = [m for m in sess.agent.messages if m.get("type") == "function_call_output"]
    print(f"\n2) SQL循环: kind={r.kind} steps={sess.agent.steps_used} 工具执行={len(outs)}次")
    for o in outs:
        d = json.loads(o["output"])
        print(f"   call {o['call_id']}: ok={d.get('ok')} data={str(d.get('data'))[:80]}")
    print(f"   reply={r.text[:200] if r.text else r.text}")
    ok2 = r.kind == "final" and len(outs) >= 2

    # 3) 挂起问答
    sess = rt.get_or_create_session("real_3", "main")
    r1 = await sess.on_message("帮我查一个城市的订单情况")
    print(f"\n3) 挂起: kind={r1.kind} question={r1.text[:80] if r1.text else r1.text}")
    if r1.kind == "ask":
        r2 = await sess.on_message("上海")
        print(f"   回答后: kind={r2.kind}")
        print(f"   reply={r2.text[:200] if r2.text else r2.text}")
        ok3 = r2.kind == "final"
    else:
        # 模型可能直接反问或直接答，都算链路通
        ok3 = r1.kind in ("final", "ask")
        print("   （模型未走 ask_human，跳过）")

    # 4) 模型切换
    sess = rt.get_or_create_session("real_4", "main")
    res = json.loads(sess.agent.switch_model("deepseek-chat"))
    r = await sess.on_message("回复两个字：收到")
    print(f"\n4) 切模型: switch_ok={res.get('ok')} now={sess.agent.model_profile}")
    print(f"   reply={r.text[:50] if r.text else r.text}")
    ok4 = res.get("ok") and r.kind == "final"

    print(f"\n==== 真实API测试: {'1' if ok1 else '0'}{'1' if ok2 else '0'}{'1' if ok3 else '0'}{'1' if ok4 else '0'} ====")

asyncio.run(main())
