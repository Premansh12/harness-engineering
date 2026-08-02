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

## How to use this repository

You only need two things: a way to read the HTML lessons and a Python 3 interpreter to run the walkthroughs. A code editor that opens the `.html` files and a terminal are enough. Below are setup paths for five common setups — pick whichever you already have.

> **Heads-up on the walkthroughs:** they run against a scripted `FakeModel` — **Python 3 standard library only, no `pip install`, no API key, no network, no cost.** They finish in under a second. That is deliberate, not a cut corner: you are studying *harness* behaviour, so the model is held perfectly constant. Every figure quoted in the lessons is real output from these scripts.
>
> **Heads-up on Windows:** the walkthroughs shell out to a few POSIX commands (`wc`, `ls`, `cat`). On native Windows `cmd.exe` / PowerShell those don't exist, so the lab runtime **shims them** to equivalent Windows commands under the hood. The lessons still teach the harness mechanics — allow-lists, blocking, exit codes — and the observed behaviour is identical. No action needed from you; just run them from a terminal with Python 3 on PATH.

### Option A — Plain terminal (macOS / Linux / WSL)

```bash
git clone https://github.com/Premansh12/harness-engineering.git
cd harness-engineering
python3 --version            # any 3.9+ is fine
open index.html              # or: xdg-open index.html  (Linux)

# run a walkthrough as you reach it
python3 lab/w01_loop.py
```

If `python3` is missing, install it: `brew install python` (macOS) or your distro's package manager.

### Option B — Windows PowerShell

```powershell
git clone https://github.com/Premansh12/harness-engineering.git
cd harness-engineering
python --version             # any 3.9+; on Windows the binary is `python`

# open the landing page
start index.html

# run a walkthrough
python lab\w01_loop.py
```

If `python` isn't found, install Python 3 from [python.org](https://www.python.org/downloads/windows/) and tick **"Add Python to PATH"** during setup. For `git`, install [Git for Windows](https://git-scm.com/downloads/win).

### Option C — Claude Code

> The `npm install -g @anthropic-ai/claude-code` command is **deprecated** — Claude Code moved to a native installer. Use the official one below.

```bash
# install (macOS / Linux / WSL)
curl -fsSL https://claude.ai/install.sh | bash

# Windows PowerShell
irm https://claude.ai/install.ps1 | iex
```

Then, inside the cloned repo:

```bash
cd harness-engineering
claude
```

Inside Claude Code, point it at a lesson and a script:

```
read lessons/01-the-loop.html and explain the twelve-line agent, then run
lab/w01_loop.py and walk me through what the output shows.
```

Claude Code reads the repo as its working directory, so paths like `lab/w01_loop.py` resolve directly. The walkthroughs are deterministic — useful for asking it to explain *why* a given output appears rather than re-running with a live model.

### Option D — OpenAI Codex CLI

```bash
npm install -g @openai/codex      # requires Node.js 22+
codex --version
```

macOS users can also use Homebrew: `brew install --cask codex`. Then:

```bash
cd harness-engineering
codex
```

In Codex, the same prompt pattern works:

```
open lessons/03-context-rot.html, then run lab/w03_context.py and tell me
what the needle test reveals about compaction versus offload.
```

### Option E — Google Antigravity (agentic IDE)

Antigravity is a **standalone desktop app**, not a package you install from a terminal. Download it from the official page:

- **Download:** https://antigravity.google/download
- macOS, Windows, and Linux installers are available.

After installing, open Antigravity, point it at the cloned `harness-engineering` folder as your project, and ask it to work through a lesson + walkthrough the same way you would in Claude Code or Codex (Option C / D). The IDE gives you a file tree and chat side-by-side, which suits the read-then-run rhythm of this course.

> Where the others are CLIs you drive from a terminal, Antigravity is a GUI — pick it if you prefer not living in the shell. All five options run the identical Python walkthroughs; only the interface differs.

---

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
python3 verify.py                      # 74 link/structure checks + platform self-test
for f in lab/w0*.py; do python3 "$f" >/dev/null && echo "OK $f"; done
```

## Structure

```
index.html          syllabus and hub
sources.html        annotated source map, tiered by weight
style.css           editorial stylesheet
lessons/            10 lesson pages
lab/
  harness_lab.py    shared runtime — FakeModel, Tool, Harness, policies + Windows shim
  w01…w08_*.py      walkthroughs
verify.py           link checker + harness self-test
```

## Going beyond the fake model

Module 09 shows how to swap in a live model: implement a single `complete()` method that returns either `{"type": "text", "text": ...}` or `{"type": "tool_call", "name": ..., "args": {...}}`. Nothing else in `harness_lab.py` changes. At that point, run each walkthrough `n > 1` and report variance — a single run against a real model is an anecdote, not a measurement.

## On the sources

Harness engineering is roughly eighteen months old as a named discipline, and its canon is written almost entirely by people selling something adjacent — model providers, framework vendors, consultancies. The engineering is good; the framing is not neutral and negative results are underreported.

Each lesson separates **measured findings** from **working heuristics**. `sources.html` tiers all fifteen sources by how much weight their claims can carry, and explicitly flags three that are cited second-hand without verification. Read for mechanism, discount conclusions, verify by ablation.

Principal sources: Vivek Trivedy (LangChain), Anthropic Engineering, Birgitta Böckeler (martinfowler.com), Addy Osmani, HumanLayer, Hugo Bowne-Anderson, He et al. (Preprints.org 202603.1756).

## The through-line

Three of the four harness components Anthropic documented were **deleted within two model generations** — context resets, sprint decomposition, per-sprint evaluation. All essential on Sonnet 4.5; all dead weight by Opus 4.6.

A stale harness component does not fail loudly. It keeps working while costing you tokens for nothing. Module 09 is entirely about the deletion half of the discipline, which is the half nobody does.

## License

MIT for the course code and prose. Quoted material remains with its original authors, cited throughout.
