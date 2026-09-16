"""
DeepSeek autonomous agent - chat loop with file + shell tool access.

SAFETY MODEL (read this before using --yolo):
  - File read/write is restricted to the project root (where this script's
    parent folder lives) by default.
  - Every file write and every shell command is printed to you and requires
    a y/N confirmation before it executes.
  - --yolo skips ALL confirmations. DeepSeek then reads your prompt, decides
    what commands to run, and runs them on your machine with no human in
    the loop. Only use this in a folder you would not mind losing.
  - --unrestricted lifts the project-root file boundary (shell commands can
    already reach anywhere via `cd` regardless - the boundary only fences
    off the read_file/write_file/list_dir tools).

Usage:
    python 04_tools/deepseek_agent.py
    python 04_tools/deepseek_agent.py --yolo
    python 04_tools/deepseek_agent.py --model deepseek-v4-flash   # cheaper, less capable
"""

import os
import sys
import json
import argparse
import subprocess

import requests

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deepseek_utils import DeepSeekClient, MODEL_PRO, API_URL

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file and return its contents.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string", "description": "Path relative to the project root"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write text content to a file, overwriting it if it exists. Creates parent folders as needed.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string"},
                    "content": {"type": "string"},
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files and folders in a directory.",
            "parameters": {
                "type": "object",
                "properties": {"path": {"type": "string"}},
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell",
            "description": "Run a shell command in the project root and return stdout, stderr, and exit code.",
            "parameters": {
                "type": "object",
                "properties": {"command": {"type": "string"}},
                "required": ["command"],
            },
        },
    },
]

SYSTEM_PROMPT = (
    "You are an agent running in a local project folder on the user's own machine. "
    "You have tools to read/write files and run shell commands. Before calling a tool, "
    "state in one short line what you are about to do and why. Prefer the smallest safe "
    "action that answers the request. If the request is ambiguous or the action is "
    "destructive (deleting, overwriting something important, force-pushing, etc.), ask "
    "the user first instead of guessing."
)


def resolve_path(path, unrestricted):
    p = os.path.abspath(path) if os.path.isabs(path) else os.path.abspath(os.path.join(PROJECT_ROOT, path))
    if not unrestricted and not (p == PROJECT_ROOT or p.startswith(PROJECT_ROOT + os.sep)):
        raise PermissionError(
            "Path '" + path + "' resolves outside the project root (" + PROJECT_ROOT + "). "
            "Re-run with --unrestricted to allow this."
        )
    return p


def confirm(prompt, auto_approve):
    if auto_approve:
        print("  [auto-approved] " + prompt)
        return True
    ans = input("  " + prompt + "  Proceed? [y/N] ").strip().lower()
    return ans == "y"


def tool_read_file(args, ctx):
    p = resolve_path(args["path"], ctx["unrestricted"])
    with open(p, "r", encoding="utf-8", errors="replace") as f:
        content = f.read()
    if len(content) > 20000:
        content = content[:20000] + "\n...[truncated, file is longer]"
    return content


def tool_write_file(args, ctx):
    p = resolve_path(args["path"], ctx["unrestricted"])
    preview = args["content"][:200].replace("\n", "\\n")
    if not confirm("WRITE " + str(len(args["content"])) + " chars to " + p + "  preview: " + preview, ctx["auto_approve"]):
        return "User declined this write. Do not retry without asking."
    parent = os.path.dirname(p)
    if parent:
        os.makedirs(parent, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(args["content"])
    return "Wrote " + str(len(args["content"])) + " chars to " + p


def tool_list_dir(args, ctx):
    p = resolve_path(args["path"], ctx["unrestricted"])
    entries = sorted(os.listdir(p))
    return "\n".join(entries) if entries else "(empty directory)"


def tool_run_shell(args, ctx):
    cmd = args["command"]
    if not confirm("RUN SHELL: " + cmd, ctx["auto_approve"]):
        return "User declined this command. Do not retry without asking."
    result = subprocess.run(
        cmd, shell=True, cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=120
    )
    out = "exit=" + str(result.returncode)
    out += "\nSTDOUT:\n" + result.stdout[-4000:]
    if result.stderr:
        out += "\nSTDERR:\n" + result.stderr[-4000:]
    return out


DISPATCH = {
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "list_dir": tool_list_dir,
    "run_shell": tool_run_shell,
}


def run_agent_turn(client, messages, ctx):
    for _ in range(20):  # hard cap on tool-call rounds per user turn
        r = requests.post(
            API_URL,
            json={"model": ctx["model"], "messages": messages, "tools": TOOLS, "max_tokens": 4000},
            headers={"Authorization": "Bearer " + client.api_key, "Content-Type": "application/json"},
            timeout=180,
        )
        if r.status_code != 200:
            print("[API error] " + str(r.status_code) + " " + r.text[:500])
            return
        data = r.json()
        usage = data.get("usage", {})
        client.last_usage = usage
        client.session_tokens += usage.get("total_tokens", 0)

        choice = data["choices"][0]
        msg = choice["message"]
        messages.append(msg)

        tool_calls = msg.get("tool_calls")
        if not tool_calls:
            content = (msg.get("content") or "").strip()
            if content:
                print("\nagent> " + content + "\n")
            return

        for tc in tool_calls:
            name = tc["function"]["name"]
            try:
                fargs = json.loads(tc["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                fargs = {}
            print("  -> " + name + "(" + json.dumps(fargs)[:200] + ")")
            try:
                result = DISPATCH[name](fargs, ctx)
            except Exception as e:
                result = "ERROR: " + str(e)
            messages.append({"role": "tool", "tool_call_id": tc["id"], "content": str(result)[:8000]})
        # loop back to the model with tool results

    print("[stopped: hit 20 tool-call rounds in one turn - possible loop]")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--yolo", action="store_true", help="Skip all confirmations")
    ap.add_argument("--unrestricted", action="store_true", help="Allow file tools outside the project root")
    ap.add_argument("--model", default=MODEL_PRO)
    ap.add_argument("--prompt", default=None, help="Run one prompt non-interactively and exit")
    args = ap.parse_args()

    ctx = {"auto_approve": args.yolo, "unrestricted": args.unrestricted, "model": args.model}
    client = DeepSeekClient()

    print("DeepSeek agent  |  model=" + args.model + "  |  project root=" + PROJECT_ROOT)
    if args.yolo:
        print("!! --yolo: shell commands and writes run WITHOUT confirmation !!")
    if args.unrestricted:
        print("!! --unrestricted: file tools are not limited to the project root !!")

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if args.prompt:
        messages.append({"role": "user", "content": args.prompt})
        run_agent_turn(client, messages, ctx)
        print("[" + client.usage_report() + "]")
        return

    print("Type 'exit' to quit.\n")
    while True:
        try:
            user_input = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if user_input.lower() in ("exit", "quit"):
            break
        if not user_input:
            continue
        messages.append({"role": "user", "content": user_input})
        run_agent_turn(client, messages, ctx)
        print("[" + client.usage_report() + "]")


if __name__ == "__main__":
    main()
