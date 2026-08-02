#!/usr/bin/env python3
"""
Walkthrough 11 — The H0–H3 maturity ladder, measured.

Run:  python3 lab/w11_ladder.py

Zhong & Zhu (arXiv:2605.13357) operationalize a harness as a four-level ladder
that "progressively exposes runtime support to the agent." The observable
claim: lower levels produce only a final patch; higher levels produce
reproduction logs, failure attributions, deterministic checks, and a
structured verification report. Here you run the SAME task at each level and
count what evidence the run leaves behind.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness_lab import banner, kv


def run_at_level(level, task):
    """Return the evidence package a run at this H-level would produce.

    level 0: bare agent  -> just a final patch string
    level 1: +tools       -> patch + which files it touched
    level 2: +verify      -> + reproduction log + pass/fail check
    level 3: +audit       -> + failure attribution + episode package
    """
    evidence = {"final_patch": f"diff for '{task}'"}
    if level >= 1:
        evidence["files_touched"] = ["src/a.py", "src/b.py"]
    if level >= 2:
        evidence["repro_log"] = "pytest reproduced the bug, then it passed"
        evidence["requirement_check"] = "PASS: all 3 acceptance criteria met"
    if level >= 3:
        evidence["failure_attribution"] = "root cause: tool X returned stale cache"
        evidence["episode_package"] = "patch + repro + attribution + check, replayable"
    return evidence


banner("1. Same task, four harness levels")

task = "fix the off-by-one in the pager"
for lvl in (0, 1, 2, 3):
    ev = run_at_level(lvl, task)
    print(f"\n  H{lvl} — produced {len(ev)} evidence items:")
    for k in ev:
        print(f"      • {k}")

banner("2. What each level adds (and why it matters)")
rows = [
    ("H0", "final patch only", "no signal when it fails"),
    ("H1", "+ files touched", "you can see what changed"),
    ("H2", "+ repro log + check", "completion stops being self-asserted (Module 05)"),
    ("H3", "+ attribution + episode", "a run you can audit AND replay (Module 12/16)"),
]
for lvl, adds, why in rows:
    print(f"  {lvl:<3} {adds:<22} -> {why}")

banner("3. Where does your harness sit?")
print("""
  Count the evidence items your own setup emits per run. If the answer is
  "one final patch," you are at H0 — and the capability gap you blame on the
  model is mostly a harness gap (Module 11's whole argument).

  EXERCISE
    a) Set level=2 and read `failure_attribution` — it is absent. That is the
       H1->H2 boundary: without attribution, a failed run gives a broken patch
       and no signal about why.
    b) The episode package at H3 is exactly the training signal self-evolving
       harnesses consume (Module 14). Tie this back: observability is what
       makes evolution possible.
""")
