---
name: find-the-cause
description: "Find and fix the root cause of a bug, failing test, wrong output or slowdown: a red-capable repro first, falsifiable hypotheses, and the failing test committed before the fix. Use when something is broken, throwing, failing or slow and the cause is not known yet."
---

# find-the-cause

Every shipped line traces to runtime evidence. A change that "might help" is a hypothesis, not a fix, and it does not ship.

## 1. Red

Build one command that goes red on this exact symptom, and run it. It must be red-capable (drives the real code path and asserts the reported symptom), deterministic, fast, and runnable without me. Try in order: a failing test at the nearest seam, the project's verify skill, an HTTP or CLI script, a replayed captured payload, old-versus-new differential, `git bisect run`.

No red command, no hypotheses. If you cannot build one, stop, list what you tried, and ask for access or a captured artifact.

## 2. Minimise

Cut inputs, steps and config one at a time, rerunning the red command after each cut, until every remaining element is load-bearing.

## 3. Hypothesise

Write 3 to 5 ranked hypotheses, each falsifiable: "If X is the cause, changing Y makes the bug disappear." Show me the list; continue with your ranking if I am away.

## 4. Instrument

One variable at a time. Tag every debug log with one prefix, such as `[DEBUG-a4f2]`, and remove them all with one grep at the end. When evidence refutes a hypothesis, revert what it motivated. If two fixes failed on the same premise, attack the premise.

## 5. Fix

Only when fixing is authorized; otherwise stop and report the cause.

- Commit the failing test first. It must fail for the right reason.
- Commit the smallest fix the evidence justifies on top of it.
- Prefer no new test over a tautological one: expected values come from an independent source, never recomputed the way the code does.
- Rerun the red command: green. Run the project's verification for the affected flows. Inconclusive, or green on a different surface, is not a pass.

## Reply

What broke, the root cause and the evidence that proves it, the fix, the red and green output trimmed to the assertion, and what remains unverified. Then say whether this class of bug can be made impossible, and at which layer: code, guard or lint, hook, or rule.
