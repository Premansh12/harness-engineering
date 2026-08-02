#!/usr/bin/env python3
"""
Walkthrough 12 — Observability: trace, attribute, replay.

Run:  python3 lab/w12_observability.py

A harness you cannot see is a harness you cannot improve. This walkthrough
builds a minimal trace, computes per-step token cost, attributes a failure to
a specific step, and replays that step in isolation — the three things Module 12
says a production harness must emit per run.
"""
import sys, os, time
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness_lab import banner, kv, Trace


def fake_token_cost(text):
    # crude stand-in: ~4 chars per token
    return max(1, len(text) // 4)


banner("1. Record a run as a trace")

trace = Trace()
# (step, kind, detail, text)
scripted = [
    (1, "model", None, "I'll read the config and run the tests."),
    (2, "tool", "read(config.yaml)", "port: 8080\nretries: 3"),
    (3, "model", None, "Now I'll run pytest."),
    (4, "tool", "bash(pytest)", "FAILED tests/test_api.py::test_timeout"),
    (5, "model", None, "The timeout test failed — config retries too low."),
]
for step, kind, detail, text in scripted:
    extra = {"step": step}
    if detail:
        extra["call"] = detail
    extra["tokens"] = fake_token_cost(text)
    trace.add(kind, **extra)
    trace.events[-1]["text"] = text

print(trace.render())

banner("2. Token cost per step (where context goes)")
per_step = {}
for e in trace.events:
    if e["kind"] in ("model", "tool"):
        per_step[e.get("step")] = per_step.get(e.get("step"), 0) + e["tokens"]
for step, tok in sorted(per_step.items()):
    print(f"  step {step}: {tok} tok")
print(f"  TOTAL: {sum(per_step.values())} tok across {len(per_step)} steps")

banner("3. Failure attribution")
failed_step = next((e["step"] for e in trace.events
                    if e["kind"] == "tool" and "FAILED" in e.get("text", "")), None)
print(f"  The failing tool call is at step {failed_step}.")
print(f"  The model's next step ({(failed_step or 0)+1}) names the cause: too-low retries.")
print("  -> attribution, not just tracing: you know WHICH step broke it.")

banner("4. Replay the failing step in isolation")
print(f"  Re-running step {failed_step}'s tool call alone to debug:")
print("    bash(pytest) -> FAILED tests/test_api.py::test_timeout")
print("  Replay lets you reproduce without re-running the whole agent.")

print("""
  EXERCISE
    a) Add a 50,000-char tool result at step 4 and watch the per-step token
       number explode — that is Module 03's context-rot, now measurable.
    b) The append-only log here is also your rollback primitive (Module 16):
       to undo step 4, replay every step except 4. Observability and safety
       are the same subsystem viewed from different ends.
""")
