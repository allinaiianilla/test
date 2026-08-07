"""
内置工具集 — 文件操作、Shell 命令、代码执行。
"""

import subprocess
import os
from pathlib import Path
from typing import List

from .registry import Tool, ToolRegistry


# ============================================================
# 文件操作工具
# ============================================================
def _read_file(path: str, start_line: int = 1, end_line: int = -1) -> str:
    """
    读取文件内容。

    Args:
        path: 文件路径
        start_line: 起始行号 (1-based)，默认第1行
        end_line: 结束行号，-1 表示读到末尾
    """
    p = Path(path)
    if not p.exists():
        return f"错误: 文件不存在 '{path}'"
    if p.is_dir():
        # 如果是目录，列出内容
        return f"'{path}' 是一个目录:\n" + _list_dir(path)

    try:
        lines = p.read_text(encoding="utf-8", errors="replace").split("\n")
        total = len(lines)
        if end_line == -1:
            end_line = total
        selected = lines[start_line - 1:end_line]

        result = []
        for i, line in enumerate(selected, start_line):
            result.append(f"{i:4d}| {line}")

        header = f"📄 {path} (行 {start_line}-{min(end_line, total)} / 共 {total} 行)\n"
        return header + "\n".join(result)
    except Exception as e:
        return f"读取失败: {e}"


def _write_file(path: str, content: str) -> str:
    """
    写入文件（覆盖模式）。

    Args:
        path: 文件路径
        content: 要写入的内容
    """
    try:
        p = Path(path)
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content, encoding="utf-8")
        return f"✅ 已写入 {path} ({len(content)} 字符)"
    except Exception as e:
        return f"写入失败: {e}"


def _list_dir(path: str = ".") -> str:
    """
    列出目录内容。

    Args:
        path: 目录路径，默认当前目录
    """
    p = Path(path)
    if not p.exists():
        return f"路径不存在: {path}"

    result = [f"📂 {p.resolve()}"]
    try:
        items = sorted(p.iterdir(), key=lambda x: (not x.is_dir(), x.name))
        for item in items:
            icon = "📁" if item.is_dir() else "📄"
            try:
                size = item.stat().st_size
                size_str = f" ({_format_size(size)})" if not item.is_dir() else ""
            except OSError:
                size_str = ""
            result.append(f"  {icon} {item.name}{size_str}")
        return "\n".join(result)
    except PermissionError:
        return f"没有权限访问: {path}"


def _search_code(pattern: str, path: str = ".", file_pattern: str = "*.py") -> str:
    """
    在代码中搜索匹配的行（类似 grep）。

    Args:
        pattern: 搜索内容
        path: 搜索目录
        file_pattern: 文件名过滤，如 *.py
    """
    from fnmatch import fnmatch
    results = []
    search_path = Path(path)

    if not search_path.exists():
        return f"路径不存在: {path}"

    for f in search_path.rglob(file_pattern):
        if f.is_file():
            try:
                for i, line in enumerate(f.read_text(encoding="utf-8", errors="replace").split("\n"), 1):
                    if pattern.lower() in line.lower():
                        results.append(f"{f}:{i}: {line.strip()[:120]}")
                        if len(results) >= 50:  # 限制结果量
                            break
            except Exception:
                continue

    if not results:
        return f"未找到匹配 '{pattern}' 的内容"
    return f"🔍 找到 {len(results)} 处匹配:\n" + "\n".join(results)


# ============================================================
# Shell 命令工具
# ============================================================
def _run_shell(command: str, timeout: int = 30) -> str:
    """
    执行 Shell 命令（危险操作，默认禁用）。

    Args:
        command: 要执行的命令
        timeout: 超时秒数
    """
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout,
            cwd=os.getcwd(),
        )
        output = result.stdout.strip()
        if result.stderr.strip():
            output += "\n[stderr]\n" + result.stderr.strip()
        return output or f"(退出码: {result.returncode})"
    except subprocess.TimeoutExpired:
        return f"命令超时 ({timeout}s)"
    except Exception as e:
        return f"执行失败: {e}"


# ============================================================
# Python 代码执行工具
# ============================================================
def _python_repl(code: str) -> str:
    """
    在受限环境中执行 Python 代码片段。

    安全限制：
    - 禁止 import os/subprocess/sys
    - 超时 5 秒
    - 返回 stdout 输出

    Args:
        code: Python 代码
    """
    # 简易沙箱检查
    dangerous = ["import os", "import subprocess", "__import__", "eval(", "exec(",
                 "open(", "import sys", "import shutil"]
    for d in dangerous:
        if d in code:
            return f"⛔ 拒绝执行（包含危险操作: {d}）"

    try:
        result = subprocess.run(
            ["python3", "-c", code],
            capture_output=True,
            text=True,
            timeout=5,
            cwd=os.getcwd(),
        )
        if result.returncode == 0:
            return result.stdout.strip() or "(执行成功，无输出)"
        return result.stderr.strip() or f"执行错误(退出码 {result.returncode})"
    except subprocess.TimeoutExpired:
        return "执行超时 (>5s)"
    except Exception as e:
        return f"执行失败: {e}"


# ============================================================
# 工具注册
# ============================================================
def _format_size(size_bytes: int) -> str:
    """格式化文件大小"""
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f}{unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f}TB"


def register_builtin_tools(registry: ToolRegistry) -> None:
    """
    向注册中心注册所有内置工具。
    """
    # ---- 安全工具（不需要确认）----
    registry.register(Tool(
        name="read_file",
        description="读取文件内容，查看代码",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "start_line": {"type": "integer", "description": "起始行号"},
                "end_line": {"type": "integer", "description": "结束行号，-1=末尾"},
            },
            "required": ["path"]
        },
        function=_read_file,
        dangerous=False,
    ))

    registry.register(Tool(
        name="list_dir",
        description="列出目录内容，查看项目结构",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "目录路径"}
            },
            "required": []
        },
        function=_list_dir,
        dangerous=False,
    ))

    registry.register(Tool(
        name="search_code",
        description="在项目中搜索代码（grep）",
        parameters={
            "type": "object",
            "properties": {
                "pattern": {"type": "string", "description": "搜索关键词"},
                "path": {"type": "string", "description": "搜索目录"},
                "file_pattern": {"type": "string", "description": "文件过滤，如 *.py"},
            },
            "required": ["pattern"]
        },
        function=_search_code,
        dangerous=False,
    ))

    # ---- 需确认工具 ----
    registry.register(Tool(
        name="write_file",
        description="写入/创建文件",
        parameters={
            "type": "object",
            "properties": {
                "path": {"type": "string", "description": "文件路径"},
                "content": {"type": "string", "description": "文件内容"}
            },
            "required": ["path", "content"]
        },
        function=_write_file,
        dangerous=True,
    ))

    registry.register(Tool(
        name="run_shell",
        description="执行 Shell 命令（危险）",
        parameters={
            "type": "object",
            "properties": {
                "command": {"type": "string", "description": "Shell 命令"},
                "timeout": {"type": "integer", "description": "超时秒数"}
            },
            "required": ["command"]
        },
        function=_run_shell,
        dangerous=True,
    ))

    registry.register(Tool(
        name="python_repl",
        description="执行 Python 代码片段（沙箱限制）",
        parameters={
            "type": "object",
            "properties": {
                "code": {"type": "string", "description": "Python 代码"}
            },
            "required": ["code"]
        },
        function=_python_repl,
        dangerous=True,
    ))
