# agentprod — 生产级 Agent 框架（Python / OpenAI Responses API）

从零对话推导并落地的完整 Agent 系统：单循环 → HITL → 数据工具 → 上下文管理 → 多 Agent 组合 → 聊天接口 → 模型配置化，全部代码化并通过单元测试 + 真实 API 端到端测试。

## 快速开始

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 配置模型 key（任选一家，或多家）
cp .env.example .env   # 编辑填入 key
export OPENAI_API_KEY=sk-...          # OpenAI（Responses API 原生）
# 或
export ZHIPU_API_KEY=你的key           # 智谱（免费 glm-4-flash 已实测可用）
export ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4
# 或
export DEEPSEEK_API_KEY=sk-...
export DEEPSEEK_BASE_URL=https://api.deepseek.com/v1

# 3. 初始化演示数据库
python -m agentprod.demo_db

# 4a. 终端聊天（最快体验）
python -m agentprod.cli

# 4b. 或启动 REST API 服务
python -m agentprod.api          # 等价 uvicorn agentprod.api:create_app --factory --port 8901
curl -X POST localhost:8901/chat -H 'Content-Type: application/json' \
     -d '{"text": "查询paid订单总数和总金额"}'
```

默认模型在 `config/models.yaml` 的 `default:` 配置；运行时可切换（见下文）。

## 项目结构

```
agentprod/
├── agentprod/                  # 框架包
│   ├── config.py               # 模型档案 + Agent 角色配置加载（Agent = 一份配置）
│   ├── llm.py                  # LLM 适配层：Responses API 封装 + 429/5xx 退避重试 + 模型路由器
│   ├── adapters.py             # 协议适配：Responses ↔ Chat Completions 双向翻译
│   ├── tools.py                # 工具系统：注册、批执行（并行/审批/挂起）、结果信封
│   ├── agent.py                # Agent 类：主循环、上下文压缩、spawn、序列化
│   ├── binding.py              # 会话级工具绑定：spawn/switch_model/ask_human 按角色注入
│   ├── builtin_tools.py        # 内置工具：SQL(只读)、时间、计算器、落盘、ask_human…
│   ├── runtime.py              # 运行时组装根：注册表+路由+会话管理+持久化
│   ├── api.py                  # REST 聊天接口（FastAPI）
│   ├── cli.py                  # 终端聊天（审批/进度在终端交互）
│   ├── mock_llm.py             # 本地 Mock Responses API 服务器（无 key 全链路测试）
│   └── demo_db.py              # SQLite 演示库（电商：users/products/orders）
├── config/
│   ├── models.yaml             # 模型档案：连接参数+采样参数+协议+窗口大小
│   └── agents.yaml             # Agent 角色：system prompt+工具清单+权限
├── tests/
│   └── test_agent.py           # 15 个单元测试（FakeLLM，不依赖网络）
├── data/
│   ├── e2e_mock_test.py        # 真实 HTTP 链路端到端（mock 服务器，7 场景）
│   ├── e2e_real_test.py        # 真实模型 API 端到端（4 场景）
│   └── sessions/               # 会话持久化（自动生成）
├── requirements.txt
└── README.md
```

## 架构：一次对话的完整链路

```
👤 用户
 ↕  （唯一聊天口：新任务 / 回答问题，同一入口）
📱 交互层  api.py（REST）或 cli.py（终端）—— 无决策，纯管道
 ↕  Session.on_message()
🧠 会话层  runtime.Session —— 按 pending 状态路由：
       无 pending → agent.run(text)        # 新任务
       有 pending → agent.resume(text)     # 回答=上次工具调用的返回值
 ↕
🤖 Agent（agent.py 主循环）
   ├── LLMRouter → LLMClient → 协议适配 → OpenAI/智谱/DeepSeek/本地
   ├── ToolExecutor 批执行（并行 + 分组 + 审批）
   │     ├── 普通工具：asyncio 并行，结果信封化，失败也留痕
   │     ├── 危险工具：执行前 approver() 审批，拒绝也产出结果
   │     └── ask_human：普通结果先落袋 → 抛 PauseForHuman → 存档挂起
   ├── 上下文压缩：估算 token > 窗口70% → 旧史摘要化（保 system/最近轮/工具配对）
   └── spawn → 子 Agent（工厂注入，非交互，深度≤2，只回收结论）
```

## 核心设计决策（对应讨论中的每个问题）

| 讨论的问题 | 落地位置 |
|---|---|
| Agent 为什么是类？配置怎么复用？ | `AgentConfig`（纯数据，YAML）+ `Agent`（运行时，只写一次）+ `agents.yaml` 注册表 |
| 大模型怎么自主查数据库？ | schema 写进 system prompt + `run_sql/list_tables/describe_table` 工具，模型自己决定查什么 |
| 大结果/多轮次怎么办？ | 四层防线：DB 聚合、强制 LIMIT+截断告知、`save_note` 落盘外置、超阈值自动压缩摘要 |
| 危险动作谁把关？ | `dangerous: True` 工具执行前必须过 `approver()`；默认无审批通道=直接拒绝（安全优先） |
| 两种"电话"怎么统一到一个聊天口？ | 会话 `pending` 状态机：用户回答被包装成 `function_call_output`（call_id 对账），`resume` 断点续跑 |
| 为什么要 raise 而不是 return？ | `PauseForHuman` 是控制流异常，从深层工具执行直接跳出到交互层，中间层零感知 |
| 一批多个工具调用怎么执行？ | 并行 `gather`；协议要求**整批凑齐**才能调 LLM；失败也产出 result；ask_human 单独分组垫后 |
| 聊天接口化解决什么？ | `ask_human` 变成"慢工具"，批处理循环无特殊分支；等待本质未消失，封装进 Session 挂起状态 |
| 子 Agent 怎么组合复用？ | `spawn_factory` 注入 + 同一个 Agent 类递归实例化；子 agent 强制非交互；深度/并行上限 |
| 大模型配置怎么做成属性+可切换？ | `ModelProfile` 档案（models.yaml）；`agent.switch_model(profile)` 会话级切换；`switch_model` 工具让模型自己切（走审批）；`LLMRouter.switch_model` 全局默认切换 |

## API 一览

| 方法 | 路径 | 说明 |
|---|---|---|
| POST | `/chat` | 发消息 `{sid?, text, role?}`；自动路由 run/resume；返回 `{kind: final\|ask\|error, reply, pending}` |
| GET | `/sessions` | 会话列表（含 pending 状态、当前模型） |
| POST | `/sessions` | 新建会话 `{role?}` |
| DELETE | `/sessions/{sid}` | 删除会话 |
| GET | `/sessions/{sid}/state` | 会话状态（消息数、步数、挂起问题） |
| POST | `/sessions/{sid}/model` | **切换模型接口** `{profile}` |
| GET | `/models` | 可用模型档案列表 |
| GET | `/health` | 健康检查 |

`kind=ask` 表示 Agent 在等用户补充信息——直接继续 `/chat` 发送答案即可（同一个口）。

## 工具清单

| 工具 | 说明 | 安全属性 |
|---|---|---|
| `get_time` / `calculator` | 时间 / AST 安全算术（非 eval） | 只读 |
| `run_sql` | 只读 SELECT，非 SELECT 拒绝，强制 LIMIT 200，字符截断 | SQL 注入防护 |
| `list_tables` / `describe_table` | 两级 schema 探索（表多时省 token） | 只读 |
| `save_note` / `read_note` | 大结果落盘外置，上下文只留路径索引 | 文件名防穿越 |
| `ask_human` | 向用户提问并挂起等待（同批普通工具先完成） | 仅顶层交互角色可见 |
| `spawn_agent` | 派子 agent（简报需自包含） | can_spawn 角色 + 深度限制 |
| `switch_model` | 会话级切换模型档案 | **dangerous**：走审批 |

## 测试

```bash
# 单元测试（15 个，FakeLLM 无网络依赖）：工具批执行、混批挂起、
# 挂起恢复、状态序列化、压缩触发、SQL 防护、模型切换、spawn
python -m pytest tests/ -v

# 真实 HTTP 链路（mock 服务器，无需 key）：
# 纯文本/SQL循环/挂起resume/混批/500重试/切换/请求格式校验
python data/e2e_mock_test.py

# 真实模型 API（需 key，已用智谱 glm-4-flash 实测通过）
export ZHIPU_API_KEY=... ZHIPU_BASE_URL=https://open.bigmodel.cn/api/paas/v4
python data/e2e_real_test.py
```

**真实 API 实测结果**（智谱 glm-4-flash，2026-08-28）：

- ✅ 纯文本对话
- ✅ SQL 工具循环：模型自主写 SQL，一次命中（92 单 / 101507.00 元，与直查数据库一致）
- ✅ ask_human 挂起 → 用户回答 → resume 续跑 → 工具输出正确入账
- ✅ 模型切换（会话级档案生效；全局切换见 `LLMRouter.switch_model`）

## 生产部署注意

1. **密钥管理**：key 只走环境变量（`api_key_env` 间接引用），不落配置文件
2. **审批通道**：`Runtime.set_interaction(approver=...)` 注入真实审批（IM 推送/审批流）；默认拒绝是安全底线，不是功能缺失
3. **持久化**：`SessionStore` 是 JSON 文件实现（含原子写），生产换 Redis/PG 只需实现 save/load/delete
4. **协议扩展**：新平台只需在 `ModelProfile.protocol` 选 `responses` / `chat-completions`；新增协议在 `adapters.py` 加一对翻译函数
5. **可观测性**：`progress` 回调挂工具播报；mock 服务器的 `/calls` 端点可审计全部请求
6. **限流**：429/5xx 自动指数退避（1s→2s→4s→8s，共 5 次尝试）
7. **免费模型提示**：glm-4-flash 指令遵循较弱，关键流程建议 `default: glm-4-plus` 或更强模型；`ask_human` 是否调用还可在工具 description 里继续加码
