#!/usr/bin/env python3
# Harness: background execution -- the model thinks while the harness waits.
"""
s08_background_tasks.py - Background Tasks

Run commands in background threads. A notification queue is drained
before each LLM call to deliver results.

    Main thread                Background thread
    +-----------------+        +-----------------+
    | agent loop      |        | task executes   |
    | ...             |        | ...             |
    | [LLM call] <---+------- | enqueue(result) |
    |  ^drain queue   |        +-----------------+
    +-----------------+

    Timeline:
    Agent ----[spawn A]----[spawn B]----[other work]----
                 |              |
                 v              v
              [A runs]      [B runs]        (parallel)
                 |              |
                 +-- notification queue --> [results injected]

Key insight: "Fire and forget -- the agent doesn't block while the command runs."
"""

import os
import subprocess
import threading
import uuid
from pathlib import Path

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv(override=True)

if os.getenv("ANTHROPIC_BASE_URL"):
    os.environ.pop("ANTHROPIC_AUTH_TOKEN", None)

WORKDIR = Path.cwd()
client = Anthropic(base_url=os.getenv("ANTHROPIC_BASE_URL"))
MODEL = os.environ["MODEL_ID"]

SYSTEM = f"You are a coding agent at {WORKDIR}. Use background_run for long-running commands."


# -- BackgroundManager: threaded execution + notification queue --
class BackgroundManager:
    # 初始化后台任务管理器，准备任务表、通知队列和线程锁。
    def __init__(self):
        # tasks 保存每个后台任务的最新状态。
        # _notification_queue 保存“已经完成、但还没通知给模型”的结果。
        # _lock 用来保护队列，避免主线程和后台线程同时修改时出错。
        self.tasks = {}  # task_id -> {status, result, command}
        self._notification_queue = []  # completed task results
        self._lock = threading.Lock()

    # 启动一个后台线程执行命令，并立即返回任务 id。
    def run(self, command: str) -> str:
        """Start a background thread, return task_id immediately."""
        # 创建一个短 task_id，立刻把任务登记为 running。
        # 真正的命令执行放到后台线程里，这样 agent 不会被阻塞。
        task_id = str(uuid.uuid4())[:8]
        self.tasks[task_id] = {"status": "running", "result": None, "command": command}
        thread = threading.Thread(
            target=self._execute, args=(task_id, command), daemon=True
        )
        thread.start()
        return f"Background task {task_id} started: {command[:80]}"

    # 在线程中真正执行命令，记录状态，并把结果放进通知队列。
    def _execute(self, task_id: str, command: str):
        """Thread target: run subprocess, capture output, push to queue."""
        # 这个函数运行在后台线程里。
        # 它负责执行命令、记录最终状态，并把摘要结果放进通知队列，
        # 等主线程下次进入 agent_loop 时再统一交给模型。
        try:
            r = subprocess.run(
                command, shell=True, cwd=WORKDIR,
                capture_output=True, text=True, timeout=300
            )
            output = (r.stdout + r.stderr).strip()[:50000]
            status = "completed"
        except subprocess.TimeoutExpired:
            output = "Error: Timeout (300s)"
            status = "timeout"
        except Exception as e:
            output = f"Error: {e}"
            status = "error"
        # 先把完整结果写回任务表，供 check(task_id) 查询。
        self.tasks[task_id]["status"] = status
        self.tasks[task_id]["result"] = output or "(no output)"
        with self._lock:
            # 通知队列里只保留精简版结果，避免一次性塞给模型太多内容。
            self._notification_queue.append({
                "task_id": task_id,
                "status": status,
                "command": command[:80],
                "result": (output or "(no output)")[:500],
            })

    # 查询后台任务状态；可查单个任务，也可列出全部任务。
    def check(self, task_id: str = None) -> str:
        """Check status of one task or list all."""
        # 如果传入 task_id，就查看单个后台任务的状态和结果。
        # 如果不传，就返回所有后台任务的概要列表。
        if task_id:
            t = self.tasks.get(task_id)
            if not t:
                return f"Error: Unknown task {task_id}"
            return f"[{t['status']}] {t['command'][:60]}\n{t.get('result') or '(running)'}"
        lines = []
        for tid, t in self.tasks.items():
            lines.append(f"{tid}: [{t['status']}] {t['command'][:60]}")
        return "\n".join(lines) if lines else "No background tasks."

    # 取出所有待通知的后台结果，并在返回后清空通知队列。
    def drain_notifications(self) -> list:
        """Return and clear all pending completion notifications."""
        # 主线程会在每次调用模型前把通知队列取空。
        # “取出并清空”必须是一个原子操作，所以这里要加锁。
        with self._lock:
            notifs = list(self._notification_queue)
            self._notification_queue.clear()
        return notifs


BG = BackgroundManager()


# -- Tool implementations --
# 校验并解析路径，确保访问范围被限制在当前工作区内。
def safe_path(p: str) -> Path:
    # 将输入路径解析到工作区内，并阻止通过 ../ 访问工作区之外的文件。
    path = (WORKDIR / p).resolve()
    if not path.is_relative_to(WORKDIR):
        raise ValueError(f"Path escapes workspace: {p}")
    return path

# 同步执行一个 shell 命令，适合短时间完成的阻塞任务。
def run_bash(command: str) -> str:
    # 同步执行 shell 命令。
    # 这个工具是阻塞的，适合短命令；长命令应该走 background_run。
    dangerous = ["rm -rf /", "sudo", "shutdown", "reboot", "> /dev/"]
    if any(d in command for d in dangerous):
        return "Error: Dangerous command blocked"
    try:
        r = subprocess.run(command, shell=True, cwd=WORKDIR,
                           capture_output=True, text=True, timeout=120)
        out = (r.stdout + r.stderr).strip()
        return out[:50000] if out else "(no output)"
    except subprocess.TimeoutExpired:
        return "Error: Timeout (120s)"

# 读取文本文件内容，并支持按行数做简单截断。
def run_read(path: str, limit: int = None) -> str:
    # 读取文本文件内容，并在需要时按行数截断。
    try:
        lines = safe_path(path).read_text().splitlines()
        if limit and limit < len(lines):
            lines = lines[:limit] + [f"... ({len(lines) - limit} more)"]
        return "\n".join(lines)[:50000]
    except Exception as e:
        return f"Error: {e}"

# 写入文件内容；如果目录不存在则自动创建。
def run_write(path: str, content: str) -> str:
    # 写入文件；如果父目录不存在则自动创建。
    try:
        fp = safe_path(path)
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_text(content)
        return f"Wrote {len(content)} bytes"
    except Exception as e:
        return f"Error: {e}"

# 对文件执行一次精确文本替换，适合做简单且可控的修改。
def run_edit(path: str, old_text: str, new_text: str) -> str:
    # 对文件做一次精确字符串替换，避免模型生成模糊 diff。
    try:
        fp = safe_path(path)
        c = fp.read_text()
        if old_text not in c:
            return f"Error: Text not found in {path}"
        fp.write_text(c.replace(old_text, new_text, 1))
        return f"Edited {path}"
    except Exception as e:
        return f"Error: {e}"


TOOL_HANDLERS = {
    # 这个映射表负责把模型请求的工具名分发到实际的 Python 实现。
    "bash":             lambda **kw: run_bash(kw["command"]),
    "read_file":        lambda **kw: run_read(kw["path"], kw.get("limit")),
    "write_file":       lambda **kw: run_write(kw["path"], kw["content"]),
    "edit_file":        lambda **kw: run_edit(kw["path"], kw["old_text"], kw["new_text"]),
    "background_run":   lambda **kw: BG.run(kw["command"]),
    "check_background": lambda **kw: BG.check(kw.get("task_id")),
}

TOOLS = [
    {"name": "bash", "description": "Run a shell command (blocking).",
     "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
    {"name": "read_file", "description": "Read file contents.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "limit": {"type": "integer"}}, "required": ["path"]}},
    {"name": "write_file", "description": "Write content to file.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "content": {"type": "string"}}, "required": ["path", "content"]}},
    {"name": "edit_file", "description": "Replace exact text in file.",
     "input_schema": {"type": "object", "properties": {"path": {"type": "string"}, "old_text": {"type": "string"}, "new_text": {"type": "string"}}, "required": ["path", "old_text", "new_text"]}},
    {"name": "background_run", "description": "Run command in background thread. Returns task_id immediately.",
     "input_schema": {"type": "object", "properties": {"command": {"type": "string"}}, "required": ["command"]}},
    {"name": "check_background", "description": "Check background task status. Omit task_id to list all.",
     "input_schema": {"type": "object", "properties": {"task_id": {"type": "string"}}}},
]


# 驱动一次完整的 agent 回合：注入后台结果、调用模型、执行工具并回传结果。
def agent_loop(messages: list):
    # 主循环：
    # 1. 先把后台任务的新结果注入上下文
    # 2. 再调用模型决定下一步
    # 3. 如果模型请求工具，就执行并把结果回传
    while True:
        # 在每次调用模型之前，先把后台任务完成通知取出来并塞回对话。
        # 这样模型即使之前“忘了等结果”，也能在下一轮自然看到后台输出。
        notifs = BG.drain_notifications()
        if notifs and messages:
            notif_text = "\n".join(
                f"[bg:{n['task_id']}] {n['status']}: {n['result']}" for n in notifs
            )
            # 这里虽然内容是系统层面的通知，但为了沿用已有消息结构，
            # 仍然作为一条 user 消息追加给模型。
            messages.append({"role": "user", "content": f"<background-results>\n{notif_text}\n</background-results>"})
        response = client.messages.create(
            model=MODEL, system=SYSTEM, messages=messages,
            tools=TOOLS, max_tokens=8000,
        )
        messages.append({"role": "assistant", "content": response.content})
        if response.stop_reason != "tool_use":
            # 模型没有继续要工具，说明当前用户回合结束。
            return
        results = []
        for block in response.content:
            if block.type == "tool_use":
                handler = TOOL_HANDLERS.get(block.name)
                try:
                    output = handler(**block.input) if handler else f"Unknown tool: {block.name}"
                except Exception as e:
                    output = f"Error: {e}"
                print(f"> {block.name}:")
                print(str(output)[:200])
                # Anthropic 的工具协议要求把工具执行结果作为 tool_result 回传。
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": str(output)})
        messages.append({"role": "user", "content": results})


# 作为脚本入口，提供一个最小可用的交互式命令行。
if __name__ == "__main__":
    # 极简交互入口：用户每输入一行，就作为一次新的 user 消息进入 agent_loop。
    history = []
    while True:
        try:
            query = input("\033[36ms08 >> \033[0m")
        except (EOFError, KeyboardInterrupt):
            break
        if query.strip().lower() in ("q", "exit", ""):
            break
        history.append({"role": "user", "content": query})
        agent_loop(history)
        response_content = history[-1]["content"]
        if isinstance(response_content, list):
            for block in response_content:
                if hasattr(block, "text"):
                    print(block.text)
        print()
