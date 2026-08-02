"""
harness_lab.py — the shared runtime for every walkthrough in this course.

Harness Engineering — a self-paced course.
Compiled by Premansh Panigrahi, August 2026.

Design rules (deliberately austere):
  * Python stdlib only. No pip install, no API key, no network.
  * A FakeModel replays scripted turns so every walkthrough is deterministic
    and free to run. Swap in a real model at the end of the course by
    implementing the same .complete(messages, tools) -> dict interface.
  * Everything you learn here is about the harness, not the model.

The model interface is intentionally the smallest thing that can be an agent:

    complete(messages, tools) -> {"type": "text",      "text": str}
                              or {"type": "tool_call", "name": str, "args": dict}
"""

from __future__ import annotations

import json
import os
import shlex
import subprocess
import time
from dataclasses import dataclass, field


# --------------------------------------------------------------------------
# 1. The model
# --------------------------------------------------------------------------

class FakeModel:
    """Replays a scripted list of turns. Deterministic, offline, free.

    script: list of dicts, each either
        {"type": "text", "text": "..."}
        {"type": "tool_call", "name": "bash", "args": {"cmd": "ls"}}

    A callable entry is invoked with the current message list, so a script can
    react to what the harness fed back (used in the back-pressure walkthrough).
    """

    def __init__(self, script, name="fake-1"):
        self.script = list(script)
        self.name = name
        self.calls = 0
        self.prompt_chars = 0

    def complete(self, messages, tools=None):
        self.calls += 1
        self.prompt_chars += sum(len(str(m.get("content", ""))) for m in messages)
        if not self.script:
            return {"type": "text", "text": "(script exhausted — stopping)"}
        turn = self.script.pop(0)
        if callable(turn):
            turn = turn(messages)
        return turn


class EchoModel:
    """A model that always answers with the last tool result. Useful as a
    control condition when you ablate harness components."""

    def __init__(self):
        self.calls = 0

    def complete(self, messages, tools=None):
        self.calls += 1
        last = messages[-1].get("content", "")
        return {"type": "text", "text": f"observed: {str(last)[:120]}"}


# --------------------------------------------------------------------------
# 2. Tools
# --------------------------------------------------------------------------

@dataclass
class Tool:
    name: str
    description: str
    fn: object
    risk: str = "low"          # low | medium | high  — used by the permission layer
    schema: dict = field(default_factory=dict)

    def spec(self):
        """What gets injected into the model's context. Every character here
        is charged against the attention budget — keep it short."""
        return {"name": self.name, "description": self.description, "schema": self.schema}


class ToolRegistry:
    def __init__(self, tools=()):
        self._tools = {t.name: t for t in tools}

    def add(self, tool):
        self._tools[tool.name] = tool
        return self

    def get(self, name):
        return self._tools.get(name)

    def specs(self):
        return [t.spec() for t in self._tools.values()]

    def context_cost(self):
        """Characters of context the tool list alone consumes."""
        return len(json.dumps(self.specs()))

    def __len__(self):
        return len(self._tools)

    def __iter__(self):
        return iter(self._tools.values())


def make_fs_tools(root):
    """Filesystem tools scoped to `root` — the most foundational harness primitive."""
    root = os.path.abspath(root)
    os.makedirs(root, exist_ok=True)

    def _safe(path):
        full = os.path.abspath(os.path.join(root, path))
        if not full.startswith(root):
            raise PermissionError(f"path escapes workspace: {path}")
        return full

    def read(path, **_):
        with open(_safe(path)) as fh:
            return fh.read()

    def write(path, content, **_):
        full = _safe(path)
        os.makedirs(os.path.dirname(full), exist_ok=True)
        with open(full, "w") as fh:
            fh.write(content)
        return f"wrote {len(content)} chars to {path}"

    def ls(path=".", **_):
        return "\n".join(sorted(os.listdir(_safe(path)))) or "(empty)"

    return [
        Tool("read",  "Read a file. args: path",              read),
        Tool("write", "Write a file. args: path, content",    write, risk="medium"),
        Tool("ls",    "List a directory. args: path",         ls),
    ]


def make_bash_tool(root, allow=("echo", "ls", "cat", "pytest", "python3", "grep", "wc", "true", "false")):
    """Bash: the general-purpose tool. Allow-listed — the harness decides what
    the model may run, not the model.

    Portability note: on native Windows (cmd.exe / PowerShell) the POSIX
    coreutils below do not exist. Rather than rewrite each walkthrough per
    platform, we shim the handful of commands the lessons actually use so the
    OBSERVED BEHAVIOUR is identical everywhere. The allow-list, the blocking,
    and the exit-code contract are what the lessons teach — not the coreutils.
    """
    root = os.path.abspath(root)
    os.makedirs(root, exist_ok=True)
    is_windows = os.name == "nt"

    def _shim(cmd):
        """Translate the few POSIX commands used in this course to Windows.
        Returns the translated command, or None to run a pure-Python fallback."""
        parts = shlex.split(cmd)
        prog, args = parts[0], parts[1:]
        if prog == "wc" and args and args[0] == "-l":
            return ("python", ["-c",
                    "import sys;print(sum(1 for _ in open(sys.argv[1])),sys.argv[1])"] + args[1:])
        if prog == "ls":
            return ("cmd", ["/c", "dir", "/b"] + args)
        if prog == "cat":
            return ("cmd", ["/c", "type"] + [a.replace("/", "\\") for a in args])
        if prog == "true":
            return ("cmd", ["/c", "exit", "0"])
        if prog == "false":
            return ("cmd", ["/c", "exit", "1"])
        if prog == "grep":
            return ("findstr", args)
        if prog == "python3":
            return ("python", args)
        return None

    def bash(cmd, **_):
        prog = shlex.split(cmd)[0] if cmd.strip() else ""
        if prog not in allow:
            return f"BLOCKED: '{prog}' is not on the allow-list {sorted(allow)}"

        run_args, use_shell = cmd, True
        if is_windows:
            shimmed = _shim(cmd)
            if shimmed:
                run_args, use_shell = [shimmed[0]] + shimmed[1], False

        try:
            out = subprocess.run(run_args, shell=use_shell, cwd=root,
                                 capture_output=True, text=True, timeout=20)
        except subprocess.TimeoutExpired:
            return "TIMEOUT after 20s"
        except FileNotFoundError as exc:
            return f"ERROR: command not available on this platform: {exc}"
        body = (out.stdout + out.stderr).strip()
        return f"exit={out.returncode}\n{body}" if body else f"exit={out.returncode}"

    return Tool("bash", "Run a shell command. args: cmd", bash, risk="high")


# --------------------------------------------------------------------------
# 3. The loop
# --------------------------------------------------------------------------

@dataclass
class Trace:
    """Observability. A harness you cannot inspect is a harness you cannot fix."""
    events: list = field(default_factory=list)
    started: float = field(default_factory=time.time)

    def add(self, kind, **data):
        self.events.append({"t": round(time.time() - self.started, 4), "kind": kind, **data})

    def count(self, kind):
        return sum(1 for e in self.events if e["kind"] == kind)

    def render(self):
        lines = []
        for e in self.events:
            kind = e["kind"]
            if kind == "tool_call":
                lines.append(f"  [{e['t']:>6.3f}] tool  {e['name']}({_short(e.get('args'))})")
            elif kind == "tool_result":
                lines.append(f"  [{e['t']:>6.3f}]   ->  {_short(e.get('result'), 90)}")
            elif kind == "text":
                lines.append(f"  [{e['t']:>6.3f}] say   {_short(e.get('text'), 90)}")
            else:
                lines.append(f"  [{e['t']:>6.3f}] {kind:<5} {_short({k: v for k, v in e.items() if k not in ('t','kind')}, 90)}")
        return "\n".join(lines)


def _short(v, n=70):
    s = str(v).replace("\n", "⏎")
    return s if len(s) <= n else s[: n - 1] + "…"


class Harness:
    """Tools in a loop, plus everything that makes the loop survivable:
    stop conditions, budgets, permissions, hooks, context policy, tracing.

    Every constructor argument is a harness design decision. Turn them off one
    at a time to feel what each is load-bearing for — that is the ablation
    exercise in Module 09.
    """

    def __init__(
        self,
        model,
        tools,
        system="You are a coding agent.",
        max_steps=12,                 # stop condition: hard step budget
        max_tool_chars=1200,          # context policy: truncate fat tool output
        approve=None,                 # permission gate: fn(tool, args) -> bool
        hooks=None,                   # {"post_tool": fn(name,args,result)->str|None}
        context_policy=None,          # fn(messages) -> messages
        trace=None,
    ):
        self.model = model
        self.tools = tools if isinstance(tools, ToolRegistry) else ToolRegistry(tools)
        self.system = system
        self.max_steps = max_steps
        self.max_tool_chars = max_tool_chars
        self.approve = approve
        self.hooks = hooks or {}
        self.context_policy = context_policy
        self.trace = trace or Trace()
        self.messages = [{"role": "system", "content": system}]

    # -- the loop ---------------------------------------------------------

    def run(self, task):
        self.messages.append({"role": "user", "content": task})
        self.trace.add("task", text=task)

        for step in range(self.max_steps):
            if self.context_policy:
                self.messages = self.context_policy(self.messages)

            out = self.model.complete(self.messages, self.tools.specs())

            if out["type"] == "text":
                self.trace.add("text", text=out["text"])
                self.messages.append({"role": "assistant", "content": out["text"]})
                return {"status": "done", "answer": out["text"], "steps": step + 1}

            name, args = out["name"], out.get("args", {})
            self.trace.add("tool_call", name=name, args=args)
            result = self._dispatch(name, args)

            # post-tool hook: deterministic control flow the model cannot skip
            hook = self.hooks.get("post_tool")
            if hook:
                extra = hook(name, args, result)
                if extra:
                    self.trace.add("hook", name=name, injected=extra)
                    result = f"{result}\n[hook] {extra}"

            if len(result) > self.max_tool_chars:
                kept = self.max_tool_chars // 2
                result = (result[:kept] + f"\n… [{len(result) - self.max_tool_chars} chars offloaded] …\n"
                          + result[-kept:])
                self.trace.add("truncate", name=name)

            self.trace.add("tool_result", result=result)
            self.messages.append({"role": "assistant", "content": f"[tool_call] {name} {json.dumps(args)}"})
            self.messages.append({"role": "tool", "content": result})

        self.trace.add("stop", reason="step_budget_exhausted")
        return {"status": "budget_exhausted", "answer": None, "steps": self.max_steps}

    def _dispatch(self, name, args):
        tool = self.tools.get(name)
        if tool is None:
            return f"ERROR: no such tool '{name}'. Available: {[t.name for t in self.tools]}"
        if self.approve and not self.approve(tool, args):
            self.trace.add("denied", name=name, args=args)
            return f"DENIED: '{name}' requires approval and it was refused."
        try:
            return str(tool.fn(**args))
        except Exception as exc:                      # a crashing tool must not kill the loop
            self.trace.add("tool_error", name=name, error=repr(exc))
            return f"ERROR from {name}: {exc!r}"

    # -- introspection ----------------------------------------------------

    def context_chars(self):
        return sum(len(str(m["content"])) for m in self.messages)

    def report(self):
        return {
            "model_calls": getattr(self.model, "calls", None),
            "tool_calls": self.trace.count("tool_call"),
            "denied": self.trace.count("denied"),
            "errors": self.trace.count("tool_error"),
            "truncations": self.trace.count("truncate"),
            "context_chars": self.context_chars(),
        }


# --------------------------------------------------------------------------
# 4. Context policies (Module 03)
# --------------------------------------------------------------------------

def no_policy(messages):
    """Baseline: append everything forever. Watch it rot."""
    return messages


def compact_after(threshold_chars=2500, keep_last=4):
    """Summarize-in-place: replace the middle of the transcript with a note.
    Cheap, lossy, irreversible — which is exactly the tradeoff to feel."""
    def policy(messages):
        size = sum(len(str(m["content"])) for m in messages)
        if size <= threshold_chars:
            return messages
        head, tail = messages[:1], messages[-keep_last:]
        dropped = len(messages) - len(head) - len(tail)
        note = {"role": "system",
                "content": f"[compacted {dropped} earlier messages — "
                           f"{size} chars of history summarized away]"}
        return head + [note] + tail
    return policy


def offload_to_files(workspace, threshold_chars=2500, keep_last=4):
    """Better: write the dropped history to disk so it is recoverable.
    Reduce in context, but keep the bytes addressable."""
    os.makedirs(workspace, exist_ok=True)
    state = {"n": 0}

    def policy(messages):
        size = sum(len(str(m["content"])) for m in messages)
        if size <= threshold_chars:
            return messages
        head, tail = messages[:1], messages[-keep_last:]
        middle = messages[1:-keep_last]
        state["n"] += 1
        path = os.path.join(workspace, f"history-{state['n']:02d}.log")
        with open(path, "w") as fh:
            for m in middle:
                fh.write(f"{m['role']}: {m['content']}\n")
        note = {"role": "system",
                "content": f"[offloaded {len(middle)} messages to {path} — "
                           f"read that file if you need the detail]"}
        return head + [note] + tail
    return policy


# --------------------------------------------------------------------------
# 5. Verification / back-pressure helpers (Module 05)
# --------------------------------------------------------------------------

def silent_on_success(cmd, workspace):
    """The context-efficient verification contract:
    success is SILENT, failure is LOUD. Returns (ok, message)."""
    out = subprocess.run(cmd, shell=True, cwd=workspace, capture_output=True, text=True)
    if out.returncode == 0:
        return True, ""
    return False, (out.stdout + out.stderr).strip()[:1500]


def generator_evaluator(generator, evaluator, task, rounds=3, threshold=8):
    """Anthropic's GAN-shaped pattern: separate the agent doing the work from
    the agent judging it. Returns the transcript of the negotiation."""
    log, artifact = [], None
    for r in range(1, rounds + 1):
        artifact = generator(task, artifact, log)
        score, critique = evaluator(artifact)
        log.append({"round": r, "score": score, "critique": critique})
        if score >= threshold:
            return {"passed": True, "rounds": r, "artifact": artifact, "log": log}
    return {"passed": False, "rounds": rounds, "artifact": artifact, "log": log}


# --------------------------------------------------------------------------
# 6. Tiny helpers for the walkthroughs
# --------------------------------------------------------------------------

def banner(title):
    print("\n" + "═" * 68)
    print(f"  {title}")
    print("═" * 68)


def kv(d, indent="  "):
    for k, v in d.items():
        print(f"{indent}{k:<16} {v}")
