#!/usr/bin/env python3
"""Verify the course: every internal link resolves, every referenced lab file exists."""
import os, re, sys

ROOT = os.path.dirname(os.path.abspath(__file__))
problems, checked = [], 0

html_files = []
for dirpath, _, names in os.walk(ROOT):
    if "_ws" in dirpath:
        continue
    for n in names:
        if n.endswith(".html"):
            html_files.append(os.path.join(dirpath, n))

for path in sorted(html_files):
    rel = os.path.relpath(path, ROOT)
    with open(path) as fh:
        html = fh.read()

    # internal hrefs
    for href in re.findall(r'href="([^"]+)"', html):
        if href.startswith(("http://", "https://", "#", "mailto:")):
            continue
        checked += 1
        target = os.path.normpath(os.path.join(os.path.dirname(path), href))
        if not os.path.exists(target):
            problems.append(f"{rel}: broken href -> {href}")

    # referenced lab scripts
    for script in set(re.findall(r'lab/(w\d+_\w+\.py)', html)):
        checked += 1
        if not os.path.exists(os.path.join(ROOT, "lab", script)):
            problems.append(f"{rel}: missing script -> lab/{script}")

    # unclosed tag sanity
    for tag in ("div", "body", "html", "pre", "table"):
        o = len(re.findall(rf"<{tag}[\s>]", html))
        c = len(re.findall(rf"</{tag}>", html))
        if o != c:
            problems.append(f"{rel}: <{tag}> {o} open vs {c} close")

    if 'href="../style.css"' not in html and 'href="style.css"' not in html:
        problems.append(f"{rel}: no stylesheet link")

    # quiz / assets wiring for lessons
    if rel not in ("index.html", "sources.html"):
        n_quizzes = len(re.findall(r'class="quiz"', html))
        n_q = len(re.findall(r'class="q"', html))
        if 'src="../assets.js"' not in html and 'src="assets.js"' not in html:
            problems.append(f"{rel}: no assets.js script (quizzes won't run)")
        if n_quizzes == 0 and n_q > 0:
            problems.append(f"{rel}: has .q blocks but no .quiz wrapper")
        # validate each answer index is within the option count (per .q block)
        for qblock in re.findall(r'(<div class="q"[^>]*>.*?)(?=<div class="q"|</div>\s*<div class="quiz"|</div>\s*</div>)', html, re.S):
            am = re.search(r'data-answer="(\d+)"', qblock)
            if not am:
                problems.append(f"{rel}: .q block missing data-answer")
                continue
            nopt = len(re.findall(r'class="opt"', qblock))
            if int(am.group(1)) >= nopt:
                problems.append(f"{rel}: quiz answer {am.group(1)} out of range for {nopt} options")
    elif rel == "index.html":
        if 'id="scoreboard"' not in html:
            problems.append("index.html: missing #scoreboard mount")
        if 'src="assets.js"' not in html:
            problems.append("index.html: no assets.js (progress won't render)")

print(f"html files : {len(html_files)}")
print(f"checks     : {checked}")

# --- cross-platform sanity: the bash shim must translate the POSIX commands
# --- the walkthroughs use, and the security contract must hold everywhere.
sys.path.insert(0, os.path.join(ROOT, "lab"))
try:
    import harness_lab
    t = harness_lab.make_bash_tool(os.path.join(ROOT, "lab", "_ws_verify"),
                                   allow=("echo", "ls"))
    if not t.fn(cmd="rm -rf /").startswith("BLOCKED"):
        problems.append("bash tool: allow-list failed to block 'rm'")
    if "exit=0" not in t.fn(cmd="echo ok"):
        problems.append("bash tool: allow-listed 'echo' did not succeed")
    print(f"platform   : {os.name} — bash allow-list and exit contract OK")
except Exception as exc:
    problems.append(f"harness_lab import/self-test failed: {exc!r}")

if problems:
    print(f"\nPROBLEMS ({len(problems)}):")
    for p in problems:
        print("  -", p)
    sys.exit(1)
print("\nAll internal links resolve. All referenced scripts exist. Tags balanced.")
