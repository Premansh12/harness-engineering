#!/usr/bin/env python3
"""
Walkthrough 05 — Back-pressure: silent success, loud failure.

Run:  python3 lab/w05_backpressure.py

Two experiments:
  A. verbose vs silent verification — measures the context cost of a green test run
  B. self-evaluation vs a separate skeptical evaluator — measures the leniency gap
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness_lab import (FakeModel, Tool, Harness, banner,
                         generator_evaluator, kv)

WS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ws05")
os.makedirs(WS, exist_ok=True)


# ============================================================ A. output shape
banner("A. The shape of a verification signal")

PASSING_SUITE = "\n".join(f"tests/test_module_{i//10}.py::test_case_{i} PASSED" for i in range(220))
FAILING_TAIL = ("tests/test_auth.py::test_expired_token FAILED\n"
                "E   AssertionError: expected 401, got 200\n"
                "E   at auth/middleware.py:88")


def verbose_tests(**_):
    """The naive tool: dump everything."""
    return PASSING_SUITE + "\n220 passed in 4.1s"


def silent_tests(fail=False, **_):
    """The context-efficient contract: nothing on success."""
    if fail:
        return f"exit=1\n{FAILING_TAIL}"
    return "exit=0"


for label, tool in (("verbose (dump all)", verbose_tests), ("silent on success", silent_tests)):
    h = Harness(
        FakeModel([
            {"type": "tool_call", "name": "test", "args": {}},
            {"type": "text", "text": "Tests are green, proceeding."},
        ]),
        [Tool("test", "Run the test suite.", tool)],
        max_tool_chars=10 ** 9,
    )
    h.run("run the tests")
    print(f"  {label:<22} context after one green run: {h.context_chars():>8,} chars")

print("""
  Same information content — 'everything passed' — at a ~500x difference in
  context cost. HumanLayer's reported failure: 4,000 lines of passing tests
  flooded the window and the agent started hallucinating about files it had
  just read. Success must be silent.

  And failure must be loud AND actionable:""")

h = Harness(
    FakeModel([
        {"type": "tool_call", "name": "test", "args": {"fail": True}},
        {"type": "tool_call", "name": "test", "args": {}},
        {"type": "text", "text": "Fixed auth/middleware.py:88, suite green."},
    ]),
    [Tool("test", "Run the test suite. args: fail", silent_tests)],
    hooks={"post_tool": lambda n, a, r: ("VERIFICATION FAILED — fix before finishing"
                                         if "exit=1" in r else None)},
)
h.run("make the auth tests pass")
print(h.trace.render())
print("""
  The hook is the deterministic part. The model cannot decline to see it, cannot
  reason its way past it, and it fires whether or not the model felt like
  checking. Böckeler's term for this: a *sensor* that emits LLM-optimised
  signal — 'a positive kind of prompt injection'.
""")


# ============================================================ B. who grades?
banner("B. Self-evaluation vs a separate evaluator")

DRAFTS = [
    "Landing page: white bg, purple gradient hero, three feature cards, Inter font.",
    "Landing page: off-white, serif display headline, asymmetric 2-col grid, muted clay accents.",
    "Landing page: near-black canvas, editorial type scale, full-bleed photography, one idea per screen.",
]


def generator(task, prev, log):
    return DRAFTS[min(len(log), len(DRAFTS) - 1)]


def self_evaluator(artifact):
    """An agent grading its own work. Anthropic: 'agents tend to respond by
    confidently praising the work.'"""
    return 9, "Looks great! Clean, modern, professional. Ship it."


def skeptical_evaluator(artifact):
    """A separate agent, tuned to be hostile, grading against written criteria.
    Criteria (Anthropic's four): design quality, originality, craft, functionality."""
    penalties = 0
    notes = []
    for tell in ("purple gradient", "three feature cards", "Inter font", "white bg"):
        if tell in artifact:
            penalties += 2
            notes.append(f"generic AI-slop pattern: '{tell}'")
    score = max(1, 10 - penalties)
    return score, "; ".join(notes) or "no stock-pattern tells; distinct point of view"


for label, ev in (("self-evaluation", self_evaluator), ("separate + skeptical", skeptical_evaluator)):
    res = generator_evaluator(generator, ev, "design a landing page", rounds=3, threshold=8)
    print(f"\n  {label}")
    print(f"    passed after {res['rounds']} round(s)")
    for entry in res["log"]:
        print(f"      round {entry['round']}: score {entry['score']:>2}  {entry['critique'][:70]}")
    print(f"    shipped: {res['artifact'][:72]}")

print("""
  Self-evaluation shipped draft #1 on round one, with a 9/10 and a compliment.
  The skeptical evaluator forced two revisions and shipped draft #3.

  The mechanism is NOT that the second evaluator is smarter. It is the same
  model. What changed:
    1. separation  — the grader has no ego investment in the artifact
    2. criteria    — 'is this good?' became 'does it violate these four rules?'
    3. calibration — few-shot examples with score breakdowns reduce drift

  Anthropic's honest caveat: separation alone does not fix leniency. An LLM is
  still generous to LLM output. But tuning a standalone evaluator to be harsh is
  far more tractable than making a generator self-critical.

  COST: their full 3-agent harness ran 6 hours / $200 vs 20 min / $9 solo — 20x.
  Their conclusion: the evaluator is worth it only when the task sits BEYOND
  what the model does reliably alone. On Opus 4.6 that boundary moved outward
  and much of the scaffolding became dead weight.

  EXERCISE
    a) Add a fifth 'tell' to the skeptical evaluator. Does draft #3 still pass?
       This is how criteria drift into over-fitting.
    b) Make the evaluator hostile enough that NOTHING passes in 3 rounds. What
       does your harness do then — loop forever, or escalate to a human?
""")
