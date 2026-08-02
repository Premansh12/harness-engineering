#!/usr/bin/env python3
"""
Walkthrough 01 — The loop is the agent.

Run:  python3 lab/w01_loop.py

You will build an agent in ~15 lines, then break it three ways. The point:
"tools in a loop" is trivially small, and every hard part is a *stop condition*.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness_lab import FakeModel, Tool, Harness, banner, kv

WS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ws01")
os.makedirs(WS, exist_ok=True)


# ---------------------------------------------------------------- the loop
def minimal_loop(model, tools, task, max_steps=10):
    """The whole idea, unadorned. Everything else in this course is a patch
    on one of the failure modes of these twelve lines."""
    messages = [{"role": "user", "content": task}]
    for _ in range(max_steps):
        out = model.complete(messages)
        if out["type"] == "text":
            return out["text"]
        result = tools[out["name"]](**out.get("args", {}))
        messages.append({"role": "assistant", "content": f"call {out['name']}"})
        messages.append({"role": "tool", "content": str(result)})
    return "STOPPED: step budget exhausted"


banner("1. Twelve lines is an agent")

tools = {"add": lambda a, b: a + b, "mul": lambda a, b: a * b}
model = FakeModel([
    {"type": "tool_call", "name": "add", "args": {"a": 17, "b": 25}},
    {"type": "tool_call", "name": "mul", "args": {"a": 42, "b": 3}},
    {"type": "text", "text": "The answer is 126."},
])
print("  result:", minimal_loop(model, tools, "compute (17+25)*3"))
print("  model calls:", model.calls, " <- three round trips, not one")


# ------------------------------------------------- failure 1: no stop condition
banner("2. Failure mode: the loop that never stops")

spinner = FakeModel([{"type": "tool_call", "name": "add", "args": {"a": 1, "b": 1}}] * 50)
print("  result:", minimal_loop(spinner, tools, "loop forever", max_steps=6))
print("  Without max_steps this burns your budget until the process is killed.")
print("  Stop conditions are not a detail. They are the first harness feature.")


# ------------------------------------------------- failure 2: a tool that throws
banner("3. Failure mode: one bad tool kills the run")

def flaky(**kw):
    raise ValueError("upstream 503")

bad_tools = {"fetch": flaky}
bad_model = FakeModel([
    {"type": "tool_call", "name": "fetch", "args": {}},
    {"type": "text", "text": "unreachable"},
])
try:
    minimal_loop(bad_model, bad_tools, "fetch it")
except Exception as exc:
    print(f"  raw loop crashed: {exc!r}")
    print("  A harness converts tool errors into observations the model can act on.")


# ------------------------------------------------- the harness version
banner("4. Same task, run through the Harness class")

reg = [
    Tool("add", "Add two numbers. args: a, b", lambda a, b: a + b),
    Tool("fetch", "Fetch a URL. args: url", flaky),
]
h = Harness(
    FakeModel([
        {"type": "tool_call", "name": "fetch", "args": {"url": "https://x"}},
        {"type": "tool_call", "name": "add", "args": {"a": 2, "b": 2}},
        {"type": "text", "text": "fetch failed, but 2+2=4 so I proceeded."},
    ]),
    reg,
    max_steps=8,
)
out = h.run("fetch https://x then add 2+2")
print(h.trace.render())
print(f"\n  status: {out['status']}   answer: {out['answer']}")
print("\n  report:")
kv(h.report(), "    ")

print("""
  READ THE TRACE. The tool raised, the harness caught it, turned it into a
  string observation, and the model routed around it. That recovery path is
  harness code — the model contributed nothing to it.

  EXERCISE
    a) Set max_steps=1 above. What status comes back, and why is that the
       correct behaviour rather than an error?
    b) Add a third tool that returns 50,000 characters. Watch `truncations`
       in the report go to 1. Then set max_tool_chars=10**9 and watch
       context_chars explode. That is Module 03 in one line.
""")
