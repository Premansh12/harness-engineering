#!/usr/bin/env python3
"""
Walkthrough 03 — Context rot, measured. Three policies, same run.

Run:  python3 lab/w03_context.py

Compares no policy / compaction / offload-to-file on an identical trajectory
and prints what each costs and what each destroys.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness_lab import (FakeModel, Tool, Harness, banner,
                         no_policy, compact_after, offload_to_files)

WS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ws03")
os.makedirs(WS, exist_ok=True)

# A tool that returns a realistically fat payload — a log file, a test run,
# an API response. This is where context actually goes.
def fat_log(n=1, **_):
    return "\n".join(f"2026-08-02T09:{i:02d}:00 INFO worker-{n} processed batch {i} ok"
                     for i in range(40))

SCRIPT = ([{"type": "tool_call", "name": "logs", "args": {"n": i}} for i in range(1, 9)]
          + [{"type": "text", "text": "All eight workers healthy."}])

# The needle: a fact stated early that a later turn must recall.
NEEDLE = "CRITICAL: the deploy key rotates at 14:00 UTC — do not deploy after that."


def run(policy, label):
    h = Harness(
        FakeModel(list(SCRIPT)),
        [Tool("logs", "Fetch worker logs. args: n", fat_log)],
        system="You are an SRE agent.",
        max_tool_chars=10 ** 9,          # disable truncation so policy is the only variable
        context_policy=policy,
    )
    h.messages.append({"role": "user", "content": NEEDLE})
    h.run("check all eight workers")

    in_context = any(NEEDLE in str(m["content"]) for m in h.messages)

    # Is the needle still RECOVERABLE anywhere the agent can reach?
    on_disk = False
    store = os.path.join(WS, "offload")
    if os.path.isdir(store):
        for fn in os.listdir(store):
            with open(os.path.join(store, fn)) as fh:
                if NEEDLE in fh.read():
                    on_disk = True

    return {
        "policy": label,
        "final_chars": h.context_chars(),
        "messages": len(h.messages),
        "in_context": in_context,
        "recoverable": in_context or on_disk,
    }


banner("Three context policies, one trajectory")

# clear any offload store from a previous run so the measurement is clean
store = os.path.join(WS, "offload")
if os.path.isdir(store):
    for fn in os.listdir(store):
        os.remove(os.path.join(store, fn))

rows = [
    run(no_policy, "none (append forever)"),
    run(compact_after(2500, keep_last=4), "compaction (lossy)"),
    run(offload_to_files(store, 2500, keep_last=4), "offload to files"),
]

print(f"  {'policy':<26} {'ctx chars':>10} {'msgs':>6} {'in ctx?':>8} {'recoverable?':>13}")
print("  " + "-" * 70)
for r in rows:
    print(f"  {r['policy']:<26} {r['final_chars']:>10,} {r['messages']:>6} "
          f"{'yes' if r['in_context'] else 'no':>8} "
          f"{'YES' if r['recoverable'] else 'GONE':>13}")

print("""
  Read the table honestly:

  * none        — the needle is present, because nothing was thrown away. It is
                  also the most expensive run and gets worse without bound.
                  On a real model, recall degrades long before the window fills
                  (context rot); the fact that the token is *present* does not
                  mean the model will *use* it.
  * compaction  — cheapest context, and the needle is GONE. Irreversibly. You
                  cannot know at compaction time which tokens turn N+10 needs.
  * offload     — the same context cost as compaction, and the needle left the
                  window too — but it is on disk and addressable. The agent can
                  go get it. That is the entire difference, and it is the whole
                  argument.

  The 'recoverable?' column is the one that matters. Reducing what the model
  sees is cheap; DESTROYING what the model could ask for is the expensive
  mistake, and compaction makes it silently.
""")

path = os.path.join(WS, "offload")
if os.path.isdir(path):
    files = sorted(os.listdir(path))
    print(f"  offloaded artifacts on disk: {files}")
    if files:
        with open(os.path.join(path, files[0])) as fh:
            head = fh.read()[:200]
        print(f"  first 200 chars of {files[0]}:\n    {head.strip()[:200]}")

print("""
  EXERCISE
    a) Set keep_last=1 in the compaction policy. At what point does the agent
       lose the thread of its own task, not just the needle?
    b) Write a 'reduce' policy that keeps only the FIRST and LAST tool result
       and drops the middle. Compare needle survival to offload.
    c) LangChain's four buckets are write / select / compress / isolate.
       Which bucket is each of the three policies above? Which bucket has no
       representative here, and which walkthrough covers it? (Answer: isolate,
       w06.)
""")
