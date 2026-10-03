---
name: make-me-realize
description: "Interview me about a plan, decision or vague request until we share one understanding: rounds of numbered questions, each with your recommended answer. Use when I ask to be grilled or interviewed, or before designing something whose important decisions are still open."
disable-model-invocation: true
---

# make-me-realize

Turn what I asked for into a settled set of decisions before anyone designs or builds.

## How

1. Map the request as a decision tree: every decision branches into the decisions that depend on it.
2. Work in rounds. The frontier is every decision whose prerequisites are already settled. Ask the whole frontier in one round, numbered, each with your recommended answer and a one-line reason. A question that depends on another question still open in this round belongs to a later round.
3. Facts are your job, decisions are mine. Look up anything the repo, the tools or the docs can answer; never ask me for it. Only the questions downstream of a lookup still running wait for it.
4. After each round, recompute the frontier from my answers. Short answers like "1 sí, 2 B, 3 lo que recomiendes" are normal.
5. Stop when the frontier is empty: every branch visited, nothing silently assumed. Write the result and wait for my confirmation before acting on it.

## Round format

```
**Q1 · <title>**: <question, with options when there are any>
→ Recommended: <answer> (<one-line reason>)
```

## Result

- **Decided**: one line per decision.
- **Out of scope**: what we explicitly will not do.
- **Still unknown**: what nobody can answer yet, and what would answer it.
- **One-way doors**: decisions that are expensive to reverse. Each gets two structurally different options before we choose.

If the project has a `decisions.md`, offer to append the decisions that should outlive this session.
