#!/usr/bin/env python3
"""
Walkthrough 10 — The inclusion/exclusion test.

Run:  python3 lab/w10_definition.py

Macedo (arXiv:2606.10106) proposes necessary-and-sufficient conditions for a
system to be an agent harness, then operationalizes them as a test that
includes and excludes consistently. Here you apply that test to six real
systems and watch the boundary hold — and see where a framework sits on the
line between "toolkit you build a harness from" and "the harness itself".
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from harness_lab import banner, kv


# Necessary condition: the runtime DRIVES the loop, tools, context, safety.
# Sufficient condition: it does so as a coherent runtime, not a loose library.
def is_harness(system):
    """Apply Macedo's boundary test.

    Returns (verdict, reason). Verdict is 'harness', 'sdk', or 'not'.
    """
    drives_loop = system["drives_loop"]
    owns_tools = system["owns_tools"]
    owns_context = system["owns_context"]
    owns_safety = system["owns_safety"]
    coherent = system["coherent_runtime"]

    if drives_loop and owns_tools and owns_context and owns_safety and coherent:
        return "harness", "meets all necessary conditions as a coherent runtime"
    if drives_loop and owns_tools and not coherent:
        return "sdk", "primitives you assemble into a harness, not the runtime itself"
    return "not", "missing one or more necessary conditions"


systems = {
    "Claude Code (product)": dict(
        drives_loop=True, owns_tools=True, owns_context=True,
        owns_safety=True, coherent_runtime=True),
    "SWE-bench (eval scaffold)": dict(
        drives_loop=True, owns_tools=True, owns_context=False,
        owns_safety=False, coherent_runtime=True),
    "LangGraph (framework)": dict(
        drives_loop=True, owns_tools=True, owns_context=True,
        owns_safety=True, coherent_runtime=False),
    "OpenAI Agents SDK (library)": dict(
        drives_loop=False, owns_tools=True, owns_context=False,
        owns_safety=False, coherent_runtime=False),
    "A custom 200-line loop": dict(
        drives_loop=True, owns_tools=True, owns_context=True,
        owns_safety=True, coherent_runtime=True),
    "A standalone RAG retriever": dict(
        drives_loop=False, owns_tools=True, owns_context=False,
        owns_safety=False, coherent_runtime=False),
}

banner("1. Classify each system against the constitutive definition")

classified = {}
for name, spec in systems.items():
    verdict, reason = is_harness(spec)
    classified[name] = verdict
    print(f"  {name:<28} -> {verdict:<8} ({reason})")

banner("2. What the test separates")
for name, v in classified.items():
    tag = {
        "harness": "the target of the definition",
        "sdk": "a toolkit you build a harness FROM (Module 15)",
        "not": "not a harness — missing necessary conditions",
    }[v]
    print(f"  {name:<28} {v:<8} {tag}")

print("""
  READ THE SPLIT. SWE-bench drives a loop and calls tools, but it does not
  own context or safety — it MEASURES, it does not act. That is exactly the
  eval-harness / agent-harness distinction Module 10 draws. LangGraph owns
  the right things but is not a coherent runtime until you assemble it — so
  it is the harness only once you wire it up. The test is inclusion/exclusion,
  not vibes.

  EXERCISE
    a) Take a tool you use daily. Fill in the five booleans above. Does it pass?
    b) Change `coherent_runtime` for LangGraph to True and re-run. Does the
       verdict change? (It should — that is the point: the boundary is the
       act of assembling, not the parts.)
""")
