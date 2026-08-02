# Harness Engineering

**A self-paced course. Compiled by Premansh Panigrahi, August 2026.**

The model is one input. Everything else — the loop, the tools, the context policy, the state, the verification, the sandbox — is yours. That surface area is where most of the leverage in agent work now sits, and it has almost no textbook.

> **Agent = Model + Harness. If you're not the model, you're the harness.**
> — Vivek Trivedy, *The Anatomy of an Agent Harness*, March 2026

The sharpest available evidence for the size of this effect comes from Terminal Bench 2.0: the same Claude Opus 4.6 weights place roughly **#33 inside Claude Code and roughly #5 inside a custom harness**. Nothing about the model changed. That gap is the subject of this course.

---

## Contents

**18 lesson pages** in editorial-styled HTML · **15 runnable walkthroughs** · **scored quizzes with a progress scoreboard** · **annotated source map**

Part I is practitioner field-report; Part II is the 2026 research literature (the H-ladder, observability, self-evolving harnesses).

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
| 10 | Defining the harness *(research)* | `lab/w10_definition.py` |
| 11 | The H0–H3 maturity ladder *(research)* | `lab/w11_ladder.py` |
| 12 | Observability & tracing *(research)* | `lab/w12_observability.py` |
| 13 | Evaluation tooling *(research)* | `lab/w13_eval.py` |
| 14 | Self-evolving harnesses *(research)* | `lab/w14_self_evolving.py` |
| 15 | Frameworks compared | `lab/w15_frameworks.py` |
| 16 | Production security & HITL | `lab/w16_production.py` |
| 17 | Capstone: build → observe → evaluate → evolve | — |

## How to use this repository

Two things are enough: a way to read the HTML lessons and a Python 3 interpreter to run the walkthroughs. A browser (or a code editor that opens `.html`) and a terminal cover it. Below are setup paths for five common setups — use whichever you already have.

> **On the walkthroughs:** they run against a scripted `FakeModel` — **Python 3 standard library only, no `pip install`, no API key, no network, no cost.** They finish in under a second. That is deliberate, not a cut corner: you are studying *harness* behaviour, so the model is held perfectly constant. Every figure quoted in the lessons is real output from these scripts.

> **On Windows:** the walkthroughs shell out to a few POSIX commands (`wc`, `ls`, `cat`). On native Windows those don't exist, so the lab runtime **shims them** to equivalent Windows commands under the hood. The observed behaviour (allow-lists, blocking, exit codes) is identical. No action needed — just run them from a terminal with Python 3 on PATH.

### Option A — Plain terminal (macOS / Linux / WSL)

```bash
git clone https://github.com/Premansh12/harness-engineering.git
cd harness-engineering
python3 --version            # any 3.9+ is fine
xdg-open index.html          # or: open index.html (macOS)

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

macOS users can also use Homebrew: `brew install --cask codex`. Then, from inside the cloned repo (Codex must run inside a git repo):

```bash
cd harness-engineering
codex exec "open lessons/03-context-rot.html, then run lab/w03_context.py and tell me
what the needle test reveals about compaction versus offload." --sandbox workspace-write
```

`--sandbox workspace-write` auto-approves file changes inside the sandbox (the recommended build mode; `--full-auto` is deprecated). Use `codex exec` for one-shots; it runs and exits cleanly.

### Option E — Google Antigravity

Antigravity ships as a **desktop app** and as a CLI (`agy`). Use either — the course material is identical; only the interface changes.

**Install the app (interactive, file-tree + chat side-by-side):**

- Download from https://antigravity.google/download (macOS, Windows, Linux installers)
- Open it, point it at the cloned `harness-engineering` folder as your project
- Work through a lesson + walkthrough the same way you would in Claude Code (Option C)

**Or install just the CLI and drive it from the terminal:**

```bash
agy install                 # puts `agy` on PATH
command -v agy && agy --version
```

`agy` manages its own auth (OS keyring, or a browser sign-in prompt on first run) — no API key to paste.

**Learn from the repo with `agy` — two patterns:**

One-shot, non-interactive (good for "explain this lesson, run that script"):

```bash
cd harness-engineering
agy -p "read lessons/01-the-loop.html, run lab/w01_loop.py, and explain the three failure modes." \
     --model 'Claude Opus 4.6 (Thinking)'
```

`agy -p` prints plain text (no JSON envelope) and is bounded by `--print-timeout` (default `5m`) — there is **no** `--max-turns`. Raise it for long tasks: `--print-timeout 20m`.

Interactive, multi-turn (the read-then-run rhythm of this course — ask follow-ups, change a script, re-run):

```bash
cd harness-engineering
agy                       # opens the TUI; /open lessons/12-observability.html, then run lab/w12_observability.py
```

Inside the TUI: `/open <path>` loads a lesson, `!` runs a shell command (so `!python3 lab/w12_observability.py` runs a walkthrough without leaving the session), and `/model` switches the engine. Resume a prior session with `agy -c`. To pull in material outside the repo as context, pass `--add-dir /path/to/notes`.

> Antigravity is a GUI or a CLI; Claude Code and Codex are CLIs you drive from a shell. All five options run the identical Python walkthroughs — pick the interface you like living in.

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
python3 verify.py                      # link + quiz + platform self-test
for f in lab/w0*.py lab/w13_eval.py; do python3 "$f" >/dev/null && echo "OK $f"; done
```

## Structure

```
index.html          syllabus, hub, progress scoreboard
sources.html        annotated source map, tiered by weight
style.css           editorial stylesheet
assets.js           quiz engine + localStorage progress
assets/hero.png     syllabus screenshot banner
voices.md           harvested leader quotes (dated, linked)
lessons/            18 lesson pages (00–17)
lab/
  harness_lab.py    shared runtime — FakeModel, Tool, Harness, policies + Windows shim
  w01…w08_*.py      walkthroughs
  w10…w16_*.py      research + production walkthroughs
  w13_eval.py       runnable eval (harness-evals-shaped, stdlib only)
verify.py           link checker + harness self-test + quiz validation
```

## Going beyond the fake model

Module 09 (and the Module 17 capstone) shows how to swap in a live model: implement a single `complete()` method that returns either `{"type": "text", "text": ...}` or `{"type": "tool_call", "name": ..., "args": {...}}`. Nothing else in `harness_lab.py` changes. At that point, run each walkthrough `n > 1` and report variance — a single run against a real model is an anecdote, not a measurement.

## On the sources

Harness engineering is roughly eighteen months old as a named discipline, and its canon is written almost entirely by people selling something adjacent — model providers, framework vendors, consultancies. The engineering is good; the framing is not neutral and negative results are underreported.

Each lesson separates **measured findings** from **working heuristics** (flagged as such). `sources.html` tiers all sources by how much weight their claims can carry, and explicitly flags three cited second-hand without verification. Read for mechanism, discount conclusions, verify by ablation.

**Principal practitioner sources:** Vivek Trivedy (LangChain), Anthropic Engineering, Birgitta Böckeler (martinfowler.com), Addy Osmani, HumanLayer, Hugo Bowne-Anderson, He et al. (Preprints.org 202603.1756).

**2026 research papers (Part II):**
- Zhong & Zhu, *AI Harness Engineering* — arXiv:2605.13357 (the H0–H3 ladder, eleven responsibilities)
- Lin et al., *Agentic Harness Engineering* — arXiv:2604.25850 (AHE, three observability pillars; pass@1 69.7%→77.0%)
- Chen et al., *HarnessX* — arXiv:2606.14249 (composable + adaptive + evolvable; +14.5% avg)
- Macedo, *What makes a harness a harness* — arXiv:2606.10106 (constitutive definition)
- Microsoft Agent Framework — https://github.com/microsoft/agent-framework (compaction, todo, file memory, OTEL, shell, background agents)

> I read the abstracts and the Microsoft page, not every full PDF, and say so in the lessons. The exact Terminal Bench ranks (~#33 vs ~#5) are approximate — I did not verify them on the leaderboard directly; the magnitude is corroborated independently. Leader quotes (Osmani, Karpathy) are real posts read from public profiles on 02 Aug 2026 and linked.

## The through-line

Three of the four harness components Anthropic documented were **deleted within two model generations** — context resets, sprint decomposition, per-sprint evaluation. All essential on Sonnet 4.5; all dead weight by Opus 4.6.

A stale harness component does not fail loudly. It keeps working while costing you tokens for nothing. Module 09 is entirely about the deletion half of the discipline, which is the half nobody does.

## License

MIT for the course code and prose. Quoted material remains with its original authors, cited throughout.
