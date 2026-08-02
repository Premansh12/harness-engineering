# Harness Engineering

**A self-paced course. Compiled by Premansh Panigrahi, August 2026.**

The model is one input. Everything else — the loop, the tools, the context policy, the state, the verification, the sandbox — is yours. That surface area is where most of the leverage in agent work now sits, and it has almost no textbook.

> **Agent = Model + Harness. If you're not the model, you're the harness.**
> — Vivek Trivedy, *The Anatomy of an Agent Harness*, March 2026

The sharpest available evidence for the size of this effect comes from Terminal Bench 2.0: the same Claude Opus 4.6 weights place roughly **#33 inside Claude Code and roughly #5 inside a custom harness**. Nothing about the model changed. That gap is the subject of this course.

---

## Contents

**10 lesson pages** in editorial-styled HTML · **8 runnable walkthroughs** · **annotated source map**

| # | Module | Walkthrough |
|---|--------|-------------|
| 00 | What a harness actually is | — |
| 01 | The loop is the agent | `lab/w01_loop.py` |
| 02 | Tools, bash, and the context tax | `lab/w02_tools.py` |
| 03 | Context rot and what to do about it | `lab/w03_context.py` |
| 04 | State, memory, and the shift change | `lab/w04_handoff.py` |
| 05 | Back-pressure: silent success, loud failure | `lab/w05_backpressure.py` |
| 06 | Long horizons: subagents and loops | `lab/w06_subagents.py` |
| 07 | Permissions, sandboxes, blast radius | `lab/w07_safety.py` |
| 08 | Evaluating harnesses honestly | `lab/w08_ablation.py` |
| 09 | Ablation, and the discipline of deleting | `lab/w08_ablation.py` + capstone |

## Getting started

Open `index.html` in a browser. That's the whole thing — no build step, no dependencies.

```bash
git clone https://github.com/Premansh12/harness-engineering.git
cd harness-engineering
open index.html          # macOS
```

Then run the walkthroughs as you reach them:

```bash
python3 lab/w01_loop.py
```

**Python 3 standard library only.** No install, no API key, no network, no cost. Every walkthrough runs against a scripted `FakeModel` and finishes in under a second.

That is not a budget compromise — it is the correct experimental design. You are studying *harness* behaviour, so the model must be held perfectly constant. A real model introduces run-to-run variance that swamps the effect you are trying to see. Module 09 shows how to swap in a live model: implement one method.

## What gets measured

Every figure quoted in the lessons is real output from these scripts, not illustration:

| Measurement | Result |
|---|---|
| Tool-description tax, 120 tools | 26,310 chars (~6,577 tokens) **before the task is read** |
| Verbose vs silent green test run | 10,011 → 89 chars (**112x**) |
| Subagent context firewall | **96.2%** parent-context reduction — total tokens go *up* |
| Compaction vs offload | identical savings; only one is recoverable |
| Full ablation | each removed component degrades exactly one column |

## Verify it

```bash
python3 verify.py                      # 74 link/structure checks
for f in lab/w0*.py; do python3 "$f" >/dev/null && echo "OK $f"; done
```

## Structure

```
index.html          syllabus and hub
sources.html        annotated source map, tiered by weight
style.css           editorial stylesheet
lessons/            10 lesson pages
lab/
  harness_lab.py    shared runtime — FakeModel, Tool, Harness, policies
  w01…w08_*.py      walkthroughs
sources/            extracted primary-source text
verify.py           link and structure checker
```

## On the sources

Harness engineering is roughly eighteen months old as a named discipline, and its canon is written almost entirely by people selling something adjacent — model providers, framework vendors, consultancies. The engineering is good; the framing is not neutral and negative results are underreported.

Each lesson separates **measured findings** from **working heuristics**. `sources.html` tiers all fifteen sources by how much weight their claims can carry, and explicitly flags three that are cited second-hand without verification. Read for mechanism, discount conclusions, verify by ablation.

Principal sources: Vivek Trivedy (LangChain), Anthropic Engineering, Birgitta Böckeler (martinfowler.com), Addy Osmani, HumanLayer, Hugo Bowne-Anderson, He et al. (Preprints.org 202603.1756).

## The through-line

Three of the four harness components Anthropic documented were **deleted within two model generations** — context resets, sprint decomposition, per-sprint evaluation. All essential on Sonnet 4.5; all dead weight by Opus 4.6.

A stale harness component does not fail loudly. It keeps working while costing you tokens for nothing. Module 09 is entirely about the deletion half of the discipline, which is the half nobody does.

## License

MIT for the course code and prose. Quoted material remains with its original authors, cited throughout.
