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

print(f"html files : {len(html_files)}")
print(f"checks     : {checked}")
if problems:
    print(f"\nPROBLEMS ({len(problems)}):")
    for p in problems:
        print("  -", p)
    sys.exit(1)
print("\nAll internal links resolve. All referenced scripts exist. Tags balanced.")
