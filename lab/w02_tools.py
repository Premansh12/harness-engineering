#!/usr/bin/env python3
"""
Walkthrough 02 — Tools, bash, and the cost of a crowded toolbelt.

Run:  python3 lab/w02_tools.py

Measures the thing everyone talks about but rarely counts: how many characters
of your context window the tool list itself eats before the agent does anything.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness_lab import (FakeModel, Tool, ToolRegistry, Harness,
                         make_fs_tools, make_bash_tool, banner, kv)

WS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ws02")
os.makedirs(WS, exist_ok=True)


banner("1. The filesystem is the foundational primitive")

reg = ToolRegistry(make_fs_tools(WS)).add(make_bash_tool(WS))
h = Harness(
    FakeModel([
        {"type": "tool_call", "name": "write",
         "args": {"path": "notes.md", "content": "# findings\n- harness > model tweak\n"}},
        {"type": "tool_call", "name": "bash", "args": {"cmd": "wc -l notes.md"}},
        {"type": "tool_call", "name": "read", "args": {"path": "notes.md"}},
        {"type": "text", "text": "Wrote and verified notes.md (2 lines)."},
    ]),
    reg,
)
print(h.trace.render() or "")
out = h.run("write a note, then verify it landed")
print(h.trace.render())
print("\n  answer:", out["answer"])
print("  Durable state outside the context window is what makes session N+1 possible.")


banner("2. The allow-list: the harness decides, not the model")

danger = Harness(
    FakeModel([
        {"type": "tool_call", "name": "bash", "args": {"cmd": "rm -rf /"}},
        {"type": "tool_call", "name": "bash", "args": {"cmd": "echo still here"}},
        {"type": "text", "text": "Destructive command was refused; continued safely."},
    ]),
    reg,
)
danger.run("clean up the disk")
print(danger.trace.render())
print("\n  'rm' was never on the allow-list, so it could not run. Note the model\n"
      "  received the refusal as text and adapted. Blocking is not enough —\n"
      "  the block must be legible to the agent.")


banner("3. Counting the tool tax")

def dummy(n):
    return Tool(f"tool_{n}",
                f"Tool number {n}. Performs operation {n} on the target resource, "
                f"accepting arguments target, mode, and options.",
                lambda **kw: "ok",
                schema={"target": "string", "mode": "string", "options": "object"})

print(f"  {'tools':>6}   {'context chars':>14}   {'~tokens':>8}")
for n in (4, 12, 30, 60, 120):
    r = ToolRegistry([dummy(i) for i in range(n)])
    cost = r.context_cost()
    print(f"  {n:>6}   {cost:>14,}   {cost // 4:>8,}")

print("""
  Every one of those characters is spent before the agent reads your task, on
  every single turn, and it is charged against the same attention budget the
  actual work needs. This is the mechanism behind "too many MCP servers makes
  the agent dumber" — it is not folklore, it is arithmetic.

  The counter-pattern is progressive disclosure: ship a short index, let the
  agent pull the detail only when the task calls for it.
""")


banner("4. CLI beats MCP when the CLI is in the training data")

print("""  HumanLayer's finding, reduced to a decision rule:

    Does a well-known CLI already do this (git, gh, docker, psql, jq)?
      YES -> prompt the agent to use the CLI. Zero tool-description tax,
             composable with grep/jq, and the model already knows the syntax
             from pretraining.
      NO  -> write a thin, context-efficient tool. Return the smallest useful
             payload, not the full API response.

  They replaced the Linear MCP server with a 6-line CLI section in CLAUDE.md
  and got better results with less context spent.

  EXERCISE
    a) Add a tool whose description is 2,000 characters. Re-run section 3 and
       find how many such tools it takes to spend 10% of a 200k window.
    b) Extend the allow-list with 'git'. Does the harness now let 'git push'
       through? Should it? Write the approve() callback that says no.
""")
