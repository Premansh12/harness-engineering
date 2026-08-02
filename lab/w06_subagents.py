#!/usr/bin/env python3
"""
Walkthrough 06 — Subagents as a context firewall, and the Ralph loop.

Run:  python3 lab/w06_subagents.py

Measures the one thing that justifies subagent complexity: how much noise the
parent thread absorbs when a subtask runs inline vs isolated.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness_lab import FakeModel, Tool, Harness, banner

WS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ws06")
os.makedirs(WS, exist_ok=True)


# Each "search" returns a realistically noisy payload.
def noisy_search(q, **_):
    return "\n".join(f"[{q}] result {i}: lorem ipsum dolor sit amet, consectetur "
                     f"adipiscing elit, sed do eiusmod tempor incididunt ut labore"
                     for i in range(25))


QUERIES = ["harness definition", "context rot", "ralph loop", "back-pressure", "sandbox design"]


# ---------------------------------------------------------------- inline
banner("1. Inline: every intermediate token lands in the parent thread")

inline = Harness(
    FakeModel([{"type": "tool_call", "name": "search", "args": {"q": q}} for q in QUERIES]
              + [{"type": "text", "text": "Synthesis: harness = model + everything else."}]),
    [Tool("search", "Search the web. args: q", noisy_search)],
    max_tool_chars=10 ** 9,
)
inline.run("research harness engineering across five subtopics")
print(f"  parent context after 5 searches: {inline.context_chars():>8,} chars")
print(f"  tool calls in parent trace:      {inline.trace.count('tool_call'):>8}")


# ---------------------------------------------------------------- isolated
banner("2. Isolated: subagent burns its own window, returns a conclusion")

def spawn_subagent(q, **_):
    """A subagent is just another Harness with its own message list. The parent
    never sees the intermediate tokens — only the return value."""
    child = Harness(
        FakeModel([
            {"type": "tool_call", "name": "search", "args": {"q": q}},
            {"type": "text", "text": f"FINDING[{q}]: one-line conclusion, 3 sources."},
        ]),
        [Tool("search", "Search the web. args: q", noisy_search)],
        max_tool_chars=10 ** 9,
    )
    out = child.run(f"research: {q}")
    # what the parent pays vs what the child spent
    spawn_subagent.child_chars = getattr(spawn_subagent, "child_chars", 0) + child.context_chars()
    return out["answer"]


orch = Harness(
    FakeModel([{"type": "tool_call", "name": "delegate", "args": {"q": q}} for q in QUERIES]
              + [{"type": "text", "text": "Synthesis: harness = model + everything else."}]),
    [Tool("delegate", "Spawn a research subagent. args: q", spawn_subagent)],
    max_tool_chars=10 ** 9,
)
orch.run("research harness engineering across five subtopics")

print(f"  parent context after 5 delegations: {orch.context_chars():>8,} chars")
print(f"  total tokens burned in children:    {spawn_subagent.child_chars:>8,} chars")
print(f"  parent context REDUCTION:           "
      f"{100 * (1 - orch.context_chars() / inline.context_chars()):>7.1f}%")

print("""
  The subagent is a context firewall. The work still costs the same total
  tokens — arguably more, because each child re-pays for a system prompt — but
  the PARENT thread stays coherent, and coherence is what runs out first on
  long tasks.

  Use it when: the subtask is independent, token-heavy, and you only need its
  conclusion. Do NOT use it when the parent needs the intermediate reasoning,
  or when the subtask needs to negotiate with the parent mid-flight.

  HumanLayer's caveat, learned the hard way: micro-optimising which subagent
  gets which tools produced 'tool thrash' and WORSE results. Give children a
  sane default toolbelt.
""")


# ---------------------------------------------------------------- ralph loop
banner("3. The Ralph loop: same prompt, fresh context, until a condition holds")

STATE = os.path.join(WS, "ralph_state.txt")
open(STATE, "w").write("0")

def ralph_iteration(i):
    """Each iteration is a NEW agent with the SAME prompt. State lives on disk.
    Termination is a harness decision, evaluated outside the agent."""
    n = int(open(STATE).read())
    n += 1
    open(STATE, "w").write(str(n))
    return n

print("  running until the exit condition holds (max 10 iterations):")
for i in range(1, 11):
    n = ralph_iteration(i)
    done = n >= 4
    print(f"    iteration {i}: features_done={n}  exit_condition={'MET' if done else 'not met'}")
    if done:
        break

print("""
  That is the entire Ralph loop: `while ! done; do agent "$PROMPT"; done`.
  It is crude and it works, because a fresh context window every iteration is a
  reliable cure for incoherence. OpenAI's Codex team runs this shape in
  production; single runs go six hours, often overnight.

  Three things the loop needs that the prompt cannot provide:
    1. durable state    — otherwise iteration N+1 redoes iteration N's work
    2. an exit condition evaluated OUTSIDE the agent — never ask the agent
       'are you done?', it will say yes
    3. a budget ceiling — wall clock, dollars, or iterations

  This is where 'loop engineering' separates from harness engineering:
  the harness asks "what environment does the agent need?", the loop asks
  "what cycle keeps it on-goal, and when does it stop?"

  EXERCISE
    a) Move the exit condition INSIDE the agent (let the fake model decide when
       it is done) and script it to declare victory on iteration 2. Now you have
       reproduced Anthropic's premature-completion failure mode.
    b) Add a per-iteration cost of $0.40 and a $2.00 ceiling. Which stops first,
       the budget or the condition?
""")
