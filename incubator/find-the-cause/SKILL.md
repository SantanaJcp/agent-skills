---
name: find-the-cause
description: "Diagnose a hard bug or performance regression through a tight red-capable loop, minimization, falsifiable hypotheses, and one-variable probes without applying the production fix. Use when the cause is unknown; do not use when the fix is already specified or implementation is requested."
license: Apache-2.0
metadata:
  tags: "debugging, diagnosis, testing"
---

# Find The Cause

## Purpose

Produce an evidence-backed diagnosis and fix direction, not a production fix. Temporary diagnostic mutations are allowed and must be cleaned.

Read [the Acta artifact protocol](references/acta-protocol.md) and use [the Document scaffold](references/acta-scaffold.html).

## Process

1. **Build the feedback loop.** Read project context/ADRs, then create the fastest agent-runnable command that drives the actual bug path and asserts the user's exact symptom. Run it. Completion: name one already-run command that is red-capable, deterministic or usefully high-reproduction, fast, and specific. If no loop can be built, record attempts and request the missing access/artifact instead of hypothesizing.
2. **Reproduce and minimize.** Confirm the same symptom across runs. Remove input, config, callers, and steps one variable at a time until every remaining element is load-bearing.
3. **Rank 3–5 falsifiable hypotheses.** For each, state the prediction that would distinguish it. Show the ranking to the user; proceed with the evidence ranking if they are unavailable.
4. **Instrument one prediction at a time.** Prefer debugger/inspection, then targeted uniquely tagged logs. For performance, establish a baseline and profile/bisect instead of logging. Temporary tests, harnesses, or instrumentation may live in the workspace or working tree.
5. **Validate the cause.** A cause is Fact only after observed evidence matches its prediction and meaningful alternatives are falsified. Record the fix direction, regression-test seam, and architectural prevention opportunity without applying them.
6. **Clean and export.** Remove temporary instrumentation/harness changes unless the user explicitly authorizes preserving evidence. Recheck repository status. Write `diagnosis.md`, generate `view.html`, and export `blueprint-seed.md`.

## Guardrails

- No red-capable loop means no theory-building phase.
- Do not apply the production fix, commit a regression test, or refactor architecture.
- Do not leave debug logs, prototypes, credentials, or unrelated changes behind.
