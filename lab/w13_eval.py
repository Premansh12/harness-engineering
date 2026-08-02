#!/usr/bin/env python3
"""w13_eval.py — a minimal, dependency-free eval runner.

Mirrors the SHAPE of harness-evals / LangSmith / Langfuse experiments:
a dataset of goldens, a target that produces output, a set of metrics
that return a 0..1 score, and a comparison against a baseline.

No external services. No API key. Stdlib only — so the method is visible
without paying for a platform. Swap `TARGET` for a real agent + a real
LLM-judge metric when you go live (Module 08: run n>1, report variance).
"""
import json, re, statistics


# ---- Golden dataset (what you author) ----
GOLDENS = [
    {"input": "add 2 and 2", "expected": "4", "kind": "math"},
    {"input": "what is 10 minus 3", "expected": "7", "kind": "math"},
    {"input": "sum 5 and 5", "expected": "10", "kind": "math"},
    {"input": "multiply 3 by 4", "expected": "12", "kind": "math"},
]

# ---- Target (the system under test). Toy: extracts the numbers and the op.
def TARGET(inp):
    nums = [int(n) for n in re.findall(r"\d+", inp)]
    if "minus" in inp or "subtract" in inp:
        return str(nums[0] - nums[1])
    if "multiply" in inp or "times" in inp or "by" in inp:
        return str(nums[0] * nums[1])
    return str(nums[0] + nums[1])  # default: add


# ---- Metrics: each returns a Score in 0.0..1.0 ----
def exact_match(golden, output):
    return 1.0 if output.strip() == golden["expected"] else 0.0

def numeric_ok(golden, output):
    try:
        return 1.0 if float(output) == float(golden["expected"]) else 0.0
    except ValueError:
        return 0.0


METRICS = {"exact_match": exact_match, "numeric_ok": numeric_ok}


def evaluate(dataset, target, metrics):
    rows = []
    for g in dataset:
        out = target(g["input"])
        scores = {name: m(g, out) for name, m in metrics.items()}
        rows.append({"input": g["input"], "output": out,
                     "expected": g["expected"], "scores": scores})
    return rows


def summarize(rows):
    print(f"{'input':22} {'out':5} {'exp':5}  exact  numeric")
    print("-" * 52)
    agg = {k: [] for k in METRICS}
    for r in rows:
        print(f"{r['input']:22} {r['output']:5} {r['expected']:5}  "
              f"{r['scores']['exact_match']:.0f}     {r['scores']['numeric_ok']:.0f}")
        for k, v in r["scores"].items():
            agg[k].append(v)
    print("-" * 52)
    for k, vs in agg.items():
        print(f"  {k:12}: mean={statistics.mean(vs):.2f}  (n={len(vs)})")
    return {k: statistics.mean(vs) for k, vs in agg.items()}


if __name__ == "__main__":
    print("=== harness-evals-shaped run (stdlib only, no platform) ===")
    rows = evaluate(GOLDENS, TARGET, METRICS)
    base = summarize(rows)
    # Baseline comparison (harness-evals' compare_to_baseline shape):
    prev = {"exact_match": 0.5, "numeric_ok": 0.5}
    print("\n=== regression vs previous baseline ===")
    for k, v in base.items():
        delta = v - prev[k]
        tag = "IMPROVED" if delta > 0.05 else ("REGRESSED" if delta < -0.05 else "flat")
        print(f"  {k:12}: {prev[k]:.2f} -> {v:.2f}  ({tag})")
