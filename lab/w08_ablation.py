#!/usr/bin/env python3
"""
Walkthrough 08 — Ablation: which harness component is actually load-bearing?

Run:  python3 lab/w08_ablation.py

This is the capstone technique. You cannot reason your way to a good harness;
you remove one component at a time and measure. Everything else in this course
is hypotheses — this is the method that tests them.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness_lab import (FakeModel, Tool, Harness, banner,
                         no_policy, compact_after)

WS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ws08")
os.makedirs(WS, exist_ok=True)


# ---------------------------------------------------------------- the task
# A scripted agent that WILL misbehave unless the harness stops it:
#   - it tries a destructive command
#   - it claims success without testing
#   - it produces fat tool output
FAT = "x" * 8000


def fat_tool(**_):
    return FAT


def test_tool(fail=True, **_):
    return "exit=1\nFAILED tests/test_core.py::test_roundtrip" if fail else "exit=0"


def script():
    """Long enough that the context policy actually has something to do."""
    return ([{"type": "tool_call", "name": "bash", "args": {"cmd": "rm -rf ."}}]
            + [{"type": "tool_call", "name": "logs", "args": {}} for _ in range(4)]
            + [{"type": "tool_call", "name": "test", "args": {"fail": True}},
               {"type": "text", "text": "Done! Everything works."}])


TOOLS = lambda: [
    Tool("bash", "Run a command. args: cmd", lambda cmd, **_: f"ran {cmd}", risk="high"),
    Tool("logs", "Fetch logs.", fat_tool),
    Tool("test", "Run tests. args: fail", test_tool),
]

STRICT_APPROVE = lambda tool, args: not (tool.risk == "high" and "rm " in str(args.get("cmd", "")))
FAILURE_HOOK = lambda n, a, r: "VERIFICATION FAILED — you may not finish" if "exit=1" in r else None


CONFIGS = {
    "full harness": dict(approve=STRICT_APPROVE, hooks={"post_tool": FAILURE_HOOK},
                         max_tool_chars=1200, context_policy=compact_after(2000)),
    "− permissions": dict(approve=None, hooks={"post_tool": FAILURE_HOOK},
                          max_tool_chars=1200, context_policy=compact_after(2000)),
    "− back-pressure": dict(approve=STRICT_APPROVE, hooks={},
                            max_tool_chars=1200, context_policy=compact_after(2000)),
    "− truncation": dict(approve=STRICT_APPROVE, hooks={"post_tool": FAILURE_HOOK},
                         max_tool_chars=10**9, context_policy=compact_after(2000)),
    "− context policy": dict(approve=STRICT_APPROVE, hooks={"post_tool": FAILURE_HOOK},
                             max_tool_chars=1200, context_policy=no_policy),
    "bare loop": dict(approve=None, hooks={}, max_tool_chars=10**9, context_policy=no_policy),
}


banner("Ablation table — remove one component, measure the damage")

rows = []
for label, cfg in CONFIGS.items():
    h = Harness(FakeModel(script()), TOOLS(), max_steps=20, **cfg)
    h.run("clean up, check logs, run tests")
    rep = h.report()
    destructive_ran = any(e.get("kind") == "tool_result" and "ran rm -rf" in str(e.get("result", ""))
                          for e in h.trace.events)
    unwarned_success = h.trace.count("hook") == 0
    rows.append({
        "config": label,
        "ctx": rep["context_chars"],
        "destructive": "RAN" if destructive_ran else "blocked",
        "false_done": "YES" if unwarned_success else "no",
    })

print(f"  {'configuration':<18} {'ctx chars':>10}  {'rm -rf':>9}  {'shipped broken':>15}")
print("  " + "-" * 60)
base = rows[0]["ctx"]
for r in rows:
    delta = "" if r["config"] == "full harness" else f"  ({r['ctx'] / base:>4.1f}x)"
    print(f"  {r['config']:<18} {r['ctx']:>10,}  {r['destructive']:>9}  {r['false_done']:>15}{delta}")

print("""
  Read it as a diff against row 1. Each removed component maps to exactly one
  column going bad — which is the definition of load-bearing. A component that
  changes NO column is dead weight, and you should delete it.

  This is how Anthropic simplified their 3-agent harness: not by redesigning it,
  but by 'removing one component at a time and reviewing what impact it had'.
  Their first attempt — cutting back radically and trying creative new ideas —
  failed, and worse, made it impossible to tell which pieces were load-bearing.

  METHODOLOGY NOTES (the part that makes this science rather than vibes)

  1. Fix the model. An ablation across different models measures nothing.
  2. Run n>1. Agent runs are non-deterministic; a single run is an anecdote.
     Report variance, not just the mean.
  3. Report cost alongside outcome. A component that buys +2% at 20x cost is a
     different decision than one that buys +2% free.
  4. Re-run on every model upgrade. Anthropic's context resets were essential on
     Sonnet 4.5 and dead weight on Opus 4.5 — the failure they patched had
     vanished from the model.

  THE HARNESSCARD (He et al., preprint 202603.1756)
  When you report an agent result, report the harness too. Required fields:
    · model + version              · tool inventory & permissions
    · context policy               · feedback stack (tests, graders, humans)
    · state/memory design          · governance, sandboxing, provenance logs
    · loop & stop conditions       · eval protocol: task set, n runs, variance,
                                     outcome criteria, budget limits
  Their argument: many reported 'model gains' are partly harness-sensitive.
  Terminal Bench 2.0 — Opus 4.6 places ~#33 in Claude Code and ~#5 in a harness
  it wasn't post-trained against. Same weights. That is the size of the effect
  you are failing to control for if you omit the harness from your report.

  EXERCISE
    a) Add a 'context policy' column that measures needle survival (from w03).
       Does compaction now show a cost that the current table hides?
    b) Ablate a component you believe is essential and find it changes nothing.
       Delete it. That is the exercise.
""")
