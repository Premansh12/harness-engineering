#!/usr/bin/env python3
"""
Walkthrough 15 — Frameworks: score them, then feel what one hides.

Run:  python3 lab/w15_frameworks.py

Module 15 says: don't become dependent on a framework, but understand how each
implements the harness. Part A scores four SDKs on the six axes this course
treats as primary. Part B wraps the twelve-line loop (Module 01) in a thin
"SDK" class so you can see exactly what a framework gives you — and what it
hides (the stop condition, the error recovery, the truncation policy).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness_lab import banner, kv, FakeModel, Tool, Harness


# ---------------------------------------------------------------- Part A
AXES = ["tool_exec", "context_policy", "memory_state", "runtime_loop",
        "verification", "observability"]

frameworks = {
    "OpenAI Agents SDK":  dict(tool_exec=2, context_policy=1, memory_state=1,
                               runtime_loop=2, verification=1, observability=1),
    "LangGraph":          dict(tool_exec=2, context_policy=2, memory_state=2,
                               runtime_loop=2, verification=2, observability=2),
    "Microsoft Agent FW": dict(tool_exec=2, context_policy=2, memory_state=2,
                               runtime_loop=2, verification=2, observability=2),
    "CrewAI / AutoGen":   dict(tool_exec=2, context_policy=1, memory_state=1,
                               runtime_loop=1, verification=1, observability=1),
}

banner("A. Score four SDKs on the six axes (0=absent, 1=partial, 2=full)")

print(f"  {'framework':<18}" + "".join(f"{a[:6]:>8}" for a in AXES) + "   sum")
for name, scores in frameworks.items():
    row = "  ".join(str(scores[a]) for a in AXES)
    print(f"  {name:<18}{row}   {sum(scores.values())}")

print("""
  The sum is a rough maturity hint, NOT a ranking to trust. The point of
  Module 15: read each column against the module it came from. LangGraph and
  Microsoft score high on runtime_loop + observability because those are the
  lessons they take seriously. CrewAI scores low on runtime_loop because it
  optimizes COORDINATION (Module 06), a different object.

  EXERCISE: take the framework you actually use and fill in the AXES dict
  yourself. Where are your gaps vs. this course?
""")

# ---------------------------------------------------------------- Part B
banner("B. Wrap the twelve-line loop in a toy 'SDK'")

# A framework is, at minimum, a class that hides the loop behind .run(task).
class ToyAgentSDK:
    def __init__(self, model, tools, max_steps=10):
        self.harness = Harness(model, tools, max_steps=max_steps)

    def run(self, task):
        # The framework hides: stop condition, error recovery, truncation.
        return self.harness.run(task)

tools = [
    Tool("echo", "Echo text. args: text", lambda text: text),
]
sdk = ToyAgentSDK(
    FakeModel([
        {"type": "tool_call", "name": "echo", "args": {"text": "hello from SDK"}},
        {"type": "text", "text": "done via framework"},
    ]),
    tools,
    max_steps=6,
)
out = sdk.run("say hello")
print(f"  sdk.run() -> status={out['status']}, answer={out['answer']!r}")
print(f"  report: {sdk.harness.report()}")

print("""
  What the SDK GAVE you: one line to run an agent instead of writing the loop.
  What it HID: max_steps is now a constructor arg you might forget to set;
  the try/except that turns a tool error into an observation (Harness class)
  is invisible; the max_tool_chars truncation policy is baked in. A framework
  is a decoration on the twelve-line loop (Module 01). When its default fights
  a lesson — irreversible compaction, in-loop verification — override it.

  EXERCISE: set max_steps=1 in the ToyAgentSDK above. The loop stops after one
  tool call and returns budget_exhausted, not an error. That stop condition is
  the FIRST harness feature (Module 01) — and the SDK let you forget it exists.
""")
