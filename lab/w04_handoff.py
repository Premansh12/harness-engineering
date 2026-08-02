#!/usr/bin/env python3
"""
Walkthrough 04 — Handoff across a context reset. The shift-change problem.

Run:  python3 lab/w04_handoff.py

Simulates three sessions, each starting with zero memory of the last, and shows
what a structured artifact buys you versus a prose summary.
"""
import sys, os, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness_lab import FakeModel, Tool, Harness, make_fs_tools, banner

WS = os.path.join(os.path.dirname(os.path.abspath(__file__)), "_ws04")
os.makedirs(WS, exist_ok=True)

FEATURES = os.path.join(WS, "features.json")
PROGRESS = os.path.join(WS, "progress.txt")


# ---------------------------------------------------------------- initializer
def initializer():
    """Anthropic's first insight: the FIRST session gets a different prompt.
    Its job is not to build — it is to make the next twenty sessions possible."""
    feats = [
        {"id": 1, "desc": "User can create a new note",            "passes": False},
        {"id": 2, "desc": "Notes persist across restart",          "passes": False},
        {"id": 3, "desc": "User can search notes by substring",    "passes": False},
        {"id": 4, "desc": "Deleting a note asks for confirmation", "passes": False},
        {"id": 5, "desc": "Notes export to markdown",              "passes": False},
    ]
    with open(FEATURES, "w") as fh:
        json.dump(feats, fh, indent=2)
    with open(PROGRESS, "w") as fh:
        fh.write("session 0 (init): scaffolded features.json, empty repo, init.sh written\n")
    return feats


banner("1. Initializer agent lays the ground")
initializer()
print(f"  wrote {FEATURES}")
print(f"  wrote {PROGRESS}")
print("  5 features, all marked failing. The agent cannot 'declare victory' against\n"
      "  a checklist it is forbidden from editing except to flip `passes`.")


# ---------------------------------------------------------------- coding sessions
def session(n, structured=True):
    """A fresh agent. No memory. It must rebuild its bearings from artifacts."""
    print(f"\n  --- session {n} boots with an empty context window ---")

    if structured:
        feats = json.load(open(FEATURES))
        todo = next((f for f in feats if not f["passes"]), None)
        prior = open(PROGRESS).read().strip().splitlines()[-2:]
        print(f"  read progress.txt  -> {prior[-1] if prior else '(none)'}")
        print(f"  read features.json -> next unfinished: #{todo['id']} {todo['desc']}")
        if todo is None:
            print("  nothing left to do")
            return False
        # do the work
        todo["passes"] = True
        json.dump(feats, open(FEATURES, "w"), indent=2)
        with open(PROGRESS, "a") as fh:
            fh.write(f"session {n}: implemented + verified feature #{todo['id']} "
                     f"({todo['desc']}); tests green; committed\n")
        done = sum(f["passes"] for f in feats)
        print(f"  implemented #{todo['id']}, committed. progress: {done}/{len(feats)}")
        return done < len(feats)
    else:
        # the failure mode: prose-only handoff
        prior = open(PROGRESS).read().strip().splitlines()[-1]
        print(f"  read progress.txt -> '{prior}'")
        print("  agent looks around, sees code already exists, concludes: 'looks done!'")
        return False


banner("2. Structured handoff: five sessions, five features")
n = 1
while session(n, structured=True) and n < 10:
    n += 1

feats = json.load(open(FEATURES))
print(f"\n  final: {sum(f['passes'] for f in feats)}/{len(feats)} features passing")


banner("3. The counterfactual: prose-only handoff")
# reset to a half-done state and hand over only prose
initializer()
feats = json.load(open(FEATURES))
for f in feats[:2]:
    f["passes"] = True
json.dump(feats, open(FEATURES, "w"), indent=2)
with open(PROGRESS, "w") as fh:
    fh.write("session 1: did some good work on the notes app, it's coming along nicely\n")
session(2, structured=False)
print(f"  reality: {sum(f['passes'] for f in json.load(open(FEATURES)))}/5 features done, "
      "3 silently abandoned")

print("""
  This is Anthropic's second documented failure mode verbatim: a later agent
  sees progress, and declares the job complete. The fix is not a better prompt.
  It is an artifact with a machine-checkable definition of 'not done yet'.

  Why JSON and not markdown? Anthropic's stated reason: models are measurably
  less willing to rewrite or quietly delete entries in a JSON file than in a
  markdown checklist. The file format is a harness decision with behavioural
  consequences.

  RESET vs COMPACTION
    compaction — same agent, shortened history. Preserves flow. Does not cure
                 'context anxiety' (wrapping up early near the window limit).
    reset      — new agent, clean slate, state carried in a handoff artifact.
                 Costs orchestration complexity; cures the anxiety.
    Anthropic needed resets on Sonnet 4.5 and DROPPED them on Opus 4.5 — the
    behaviour they patched had disappeared from the model. Harness features
    expire. Re-test yours against every model upgrade.

  EXERCISE
    a) Add a feature the agent cannot actually implement. Does your loop
       terminate, or does it spin forever on feature #6? Add the stop condition.
    b) Make session() lie — mark passes=True without doing the work. What
       harness component catches that? (It is not the handoff. See w05.)
""")
