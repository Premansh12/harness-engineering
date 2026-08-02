#!/usr/bin/env python3
"""
Walkthrough 14 — The self-evolving loop (AHE, miniature).

Run:  python3 lab/w14_self_evolving.py

Lin et al. (arXiv:2604.25850): a closed loop driven by three observability
pillars. Every edit is a self-declared PREDICTION, verified against the next
round's outcome. Here you run a 10-round miniature: propose a harness edit,
predict its effect on pass@1, measure, confirm/reject. Then you ABLATE the
edit kind to localize where the gain came from — matching the paper's finding
that the win sits in tools/middleware/memory, not the system prompt.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness_lab import banner, kv


# A toy "pass@1" measurer. Real AHE distills millions of trajectory tokens;
# we use a stable function of the harness config so the loop is deterministic.
def pass_at_1(config):
    base = 69.7
    base += 4.0 if config.get("better_tool_desc") else 0.0      # tools
    base += 2.5 if config.get("smart_middleware") else 0.0      # middleware
    base += 0.8 if config.get("long_term_memory") else 0.0      # memory
    base += 0.1 if config.get("polished_prompt") else 0.0       # system prompt
    return min(base, 85.0)


# Candidate edits: each is a prediction of which component it touches.
candidates = [
    ("better_tool_desc",  "tools",          "richer CLI descriptions cut model confusion"),
    ("smart_middleware",  "middleware",     "retry+backoff middleware reduces transient fails"),
    ("long_term_memory",  "memory",         "persisted memory avoids re-deriving facts"),
    ("polished_prompt",   "system_prompt",  "a cleaner system prompt"),
]

banner("1. Ten rounds of propose -> predict -> verify")

config = {}
history = []
for rnd in range(1, 11):
    # pick the next untried candidate (AHE proposes from the evidence corpus)
    if candidates:
        key, component, prediction = candidates.pop(0)
    else:
        key, component, prediction = ("polished_prompt", "system_prompt",
                                       "no more structural edits; polish prompt")
    before = pass_at_1(config)
    config[key] = True
    after = pass_at_1(config)
    delta = after - before
    verdict = "CONFIRMED" if delta > 0 else "REJECTED"
    history.append((rnd, component, prediction, delta, verdict))
    print(f"  round {rnd:>2} | edit={component:<13} | predicted: {prediction}")
    print(f"         pass@1 {before:.1f} -> {after:.1f}  ({'+' if delta>=0 else ''}{delta:.1f})  {verdict}")

final = pass_at_1(config)
banner("2. Result")
print(f"  Evolved harness pass@1: {final:.1f}%   (started 69.7%, human baseline 71.9%)")
print(f"  {'BEATS human-designed harness' if final > 71.9 else 'below human baseline'}")

banner("3. Ablation — where did the gain come from?")
gains = {}
for rnd, component, _, delta, _ in history:
    gains[component] = gains.get(component, 0.0) + delta
print("  Contribution by component:")
for comp, g in sorted(gains.items(), key=lambda x: -x[1]):
    print(f"    {comp:<13} +{g:.1f}pp")
structural = sum(g for c, g in gains.items() if c != "system_prompt")
prompt = gains.get("system_prompt", 0.0)
print(f"\n  structural (tools/middleware/memory): +{structural:.1f}pp")
print(f"  system prompt:                        +{prompt:.1f}pp")
print("  -> gain localizes to factual harness STRUCTURE, not prose. Same lesson as Module 09.")

print("""
  EXERCISE
    a) Reorder `candidates` so the prompt edit comes first. Does the FINAL
       pass@1 change? (It shouldn't — the ablation shows the prompt barely
       matters. That is the point: structure transfers, prose doesn't.)
    b) Set every delta to 0 except `smart_middleware`. What does the loop
       conclude about where to invest next? (Middleware — the AHE engine would
       propose more middleware edits, not more prompt polish.)
""")
