"""内置工具集：ask_human、spawn_agent、switch_model、时间、算术、
落盘查询、数据库（SQLite 只读 + 强制 LIMIT）。

每个工具 = 普通函数 + 注册元数据。危险工具标 dangerous=True。
"""
from __future__ import annotations

import ast
import datetime
import json
import operator
import os
import sqlite3
import tempfile
from pathlib import Path

from .config import DATA_DIR
from .tools import ToolRegistry

OPS = {
    "+": operator.add, "-": operator.sub, "*": operator.mul,
    "/": operator.truediv, "%": operator.mod, "**": operator.pow,
}


# ---------------------------------------------------------------------- #
# 基础工具
# ---------------------------------------------------------------------- #

def get_time() -> str:
    """当前时间。"""
    now = datetime.datetime.now()
    return json.dumps({
        "iso": now.isoformat(timespec="seconds"),
        "weekday": ["周一", "周二", "周三", "周四", "周五", "周六", "周日"][now.weekday()],
    }, ensure_ascii=False)


def calculator(expression: str) -> str:
    """安全算术：只允许数字和 + - * / % ** ( )（AST 校验，非 eval）。"""
    try:
        node = ast.parse(expression, mode="eval")
        def ev(n):
            if isinstance(n, ast.Expression):
                return ev(n.body)
            if isinstance(n, ast.Constant) and isinstance(n.value, (int, float)):
                return n.value
            if isinstance(n, ast.BinOp) and type(n.op).__name__ in {"Add", "Sub", "Mult", "Div", "Mod", "Pow"}:
                sym = {"Add": "+", "Sub": "-", "Mult": "*", "Div": "/",
                       "Mod": "%", "Pow": "**"}[type(n.op).__name__]
                return OPS[sym](ev(n.left), ev(n.right))
            if isinstance(n, ast.UnaryOp) and isinstance(n.op, (ast.UAdd, ast.USub)):
                v = ev(n.operand)
                return v if isinstance(n.op, ast.UAdd) else -v
            raise ValueError(f"不允许的表达式节点: {ast.dump(n)[:60]}")
        return json.dumps({"result": ev(node)}, ensure_ascii=False)
    except Exception as e:  # noqa: BLE001
        return json.dumps({"error": f"表达式不合法: {e}"}, ensure_ascii=False)


# ---------------------------------------------------------------------- #
# 聊天交互：ask_human（挂起式问用户）
# ---------------------------------------------------------------------- #

ASK_HUMAN_DESC = (
    "向用户提出一个问题并等待回答。仅在缺少关键信息且无法从上下文推断时使用；"
    "不要用它询问用户已提供过的信息。一次只问一个问题，把需要的信息合并成一句话。"
)


# 函数本体由 ToolExecutor 特判（is_ask_human），不真正执行
def ask_human(question: str) -> str:  # pragma: no cover
    raise RuntimeError("ask_human 由执行器特判处理，不应直接调用")


# ---------------------------------------------------------------------- #
# 子 Agent
# ---------------------------------------------------------------------- #

SPAWN_DESC = (
    "派一个子 agent 去完成一项可独立的子任务（如批量搜索、数据分析、写作）。"
    "task 描述必须自包含：背景、目标、输出要求，因为子 agent 看不到当前对话。"
)


# ---------------------------------------------------------------------- #
# 模型切换
# ---------------------------------------------------------------------- #

SWITCH_DESC = (
    "切换当前会话使用的模型档案（如换成更强或更便宜的模型）。"
    "只在该会话的后续轮次生效。"
)


def list_models() -> str:
    """列出可用模型档案（占位：由 runtime 注入真实实现，覆盖此函数）。"""
    return json.dumps({"models": []}, ensure_ascii=False)


# ---------------------------------------------------------------------- #
# 落盘外置：大结果写文件，上下文只留索引
# ---------------------------------------------------------------------- #

def save_note(filename: str, content: str) -> str:
    """把大段内容写入 data/files/<filename>，返回路径索引。"""
    safe = Path(filename).name  # 防目录穿越
    d = DATA_DIR / "files"
    d.mkdir(parents=True, exist_ok=True)
    p = d / safe
    p.write_text(content, encoding="utf-8")
    return json.dumps({"ok": True, "path": str(p),
                       "bytes": len(content.encode("utf-8"))}, ensure_ascii=False)


def read_note(filename: str) -> str:
    safe = Path(filename).name
    p = DATA_DIR / "files" / safe
    if not p.exists():
        return json.dumps({"error": f"文件不存在: {safe}"}, ensure_ascii=False)
    text = p.read_text(encoding="utf-8")
    if len(text) > 24000:
        return json.dumps({"data": text[:24000],
                           "note": "已截断，请用 offset 分段读"}, ensure_ascii=False)
    return json.dumps({"data": text}, ensure_ascii=False)


# ---------------------------------------------------------------------- #
# 数据库工具（SQLite 演示库 + 只读防护 + 强制 LIMIT）
# ---------------------------------------------------------------------- #

DB_PATH = DATA_DIR / "demo.db"
_FORBIDDEN = ("insert", "update", "delete", "drop", "alter", "create",
              "replace", "attach", "pragma", "vacuum", "reindex")


def run_sql(sql: str) -> str:
    """只读 SQL：拒绝非 SELECT；自动加 LIMIT；行数/字符双重截断。"""
    s = sql.strip().rstrip(";").strip()
    if not s.lower().startswith("select") and not s.lower().startswith("with"):
        return json.dumps({"error": "只允许 SELECT / WITH 查询"}, ensure_ascii=False)
    low = s.lower()
    if any(k in low for k in _FORBIDDEN):
        # 允许 select ... from "delete_log" 这类表名误伤？演示库没有，保持严格
        return json.dumps({"error": "SQL 中含被禁止的关键字"}, ensure_ascii=False)
    if "limit" not in low:
        s += " LIMIT 200"
    try:
        conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
        try:
            conn.row_factory = sqlite3.Row
            cur = conn.execute(s)
            rows = cur.fetchmany(200)
            cols = [d[0] for d in cur.description] if cur.description else []
            data = [dict(r) for r in rows]
        finally:
            conn.close()
    except sqlite3.Error as e:
        return json.dumps({"error": f"SQL 错误: {e}"}, ensure_ascii=False)
    truncated = len(data) >= 200
    return json.dumps({
        "columns": cols, "rows": data, "row_count": len(data),
        **({"note": "结果被截断到 200 行，请缩小范围或用聚合"} if truncated else {}),
    }, ensure_ascii=False)


def list_tables() -> str:
    """列出演示数据库所有表及注释。"""
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        cur = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [r[0] for r in cur.fetchall()]
    finally:
        conn.close()
    return json.dumps({"tables": tables}, ensure_ascii=False)


def describe_table(table: str) -> str:
    """查看某张表的字段结构与示例行。"""
    safe = "".join(c for c in table if c.isalnum() or c == "_")
    if not safe:
        return json.dumps({"error": "非法表名"}, ensure_ascii=False)
    conn = sqlite3.connect(f"file:{DB_PATH}?mode=ro", uri=True)
    try:
        cur = conn.execute(f'PRAGMA table_info("{safe}")')
        cols = [{"name": r[1], "type": r[2]} for r in cur.fetchall()]
        cur2 = conn.execute(f'SELECT * FROM "{safe}" LIMIT 3')
        sample = [dict(zip([c["name"] for c in cols], r)) for r in cur2.fetchall()]
    except sqlite3.Error as e:
        return json.dumps({"error": str(e)}, ensure_ascii=False)
    finally:
        conn.close()
    return json.dumps({"table": safe, "columns": cols, "sample_rows": sample},
                      ensure_ascii=False)


# ---------------------------------------------------------------------- #
# 注册入口
# ---------------------------------------------------------------------- #

def register_builtin_tools(registry: ToolRegistry, agent_registry_names=None,
                           model_profiles=None, spawn_impl=None,
                           switch_impl=None, list_models_impl=None):
    """把内置工具挂到注册表。注入运行时回调（spawn/切换模型）。"""
    registry.register_function(
        "get_time", "获取当前日期时间（周几、几点）",
        {"type": "object", "properties": {}}, get_time, group="basic")
    registry.register_function(
        "calculator", "安全算术计算（+-*/%、幂）",
        {"type": "object", "properties": {
            "expression": {"type": "string", "description": "算术表达式"}},
            "required": ["expression"]}, calculator, group="basic")
    registry.register_function(
        "ask_human", ASK_HUMAN_DESC,
        {"type": "object", "properties": {
            "question": {"type": "string"}}, "required": ["question"]},
        ask_human, is_ask_human=True, group="chat")
    registry.register_function(
        "save_note", "把大段内容保存为文件（上下文外置），返回路径",
        {"type": "object", "properties": {
            "filename": {"type": "string"}, "content": {"type": "string"}},
            "required": ["filename", "content"]}, save_note, group="files")
    registry.register_function(
        "read_note", "读取已保存的文件内容",
        {"type": "object", "properties": {
            "filename": {"type": "string"}}, "required": ["filename"]},
        read_note, group="files")
    registry.register_function(
        "run_sql", "在演示数据库上执行只读 SELECT 查询（自动 LIMIT 200）",
        {"type": "object", "properties": {
            "sql": {"type": "string"}}, "required": ["sql"]},
        run_sql, group="db", timeout=30.0)
    registry.register_function(
        "list_tables", "列出数据库中的所有表",
        {"type": "object", "properties": {}}, list_tables, group="db")
    registry.register_function(
        "describe_table", "查看表结构字段与示例行",
        {"type": "object", "properties": {
            "table": {"type": "string"}}, "required": ["table"]},
        describe_table, group="db")

    if spawn_impl is not None:
        registry.register_function(
            "spawn_agent", SPAWN_DESC,
            {"type": "object", "properties": {
                "agent_name": {"type": "string",
                               "description": "角色名，见 agent 角色列表"},
                "task": {"type": "string", "description": "自包含任务简报"}},
                "required": ["agent_name", "task"]},
            spawn_impl, group="orchestration")
    if switch_impl is not None:
        registry.register_function(
            "switch_model", SWITCH_DESC,
            {"type": "object", "properties": {
                "profile": {"type": "string",
                            "description": "模型档案名"}},
                "required": ["profile"]},
            switch_impl, group="system", dangerous=True)
    if list_models_impl is not None:
        registry.register_function(
            "list_models", "列出可切换的模型档案及说明",
            {"type": "object", "properties": {}}, list_models_impl,
            group="system")
