---
name: retro
description: "Retrospective over my Claude Code and Codex transcripts: find the corrections I had to repeat and propose the strongest fix for each, from code to memory. Proposes only; never applies. Use when I ask for a retro, or from the weekly automation."
disable-model-invocation: true
---

# retro

You are improving the environment the agents work in, not judging one session.

## Steps

1. **Extract.** `kitchen retro --since 7d` prints my prompts from both tools with project, session and time. Widen the window when I ask.
2. **Find** what cost me attention: corrections ("no", "otra vez", "te dije", "eso está mal", "outdated"), instructions repeated across sessions, the same question asked twice, agents rebuilding the same script, and mistakes with real damage.
3. **Group** by root cause, not by wording. Keep a group with two or more occurrences, or one with real damage.
4. **Pick the strongest layer** that would have prevented it:
   1. impossible in code;
   2. guard test, lint or `kitchen check` rule;
   3. hook;
   4. the project's AGENTS.md;
   5. the global AGENTS.md;
   6. a skill;
   7. memory.

   A mechanical violation (a banned API, a file location, a command pattern) gets a deterministic check, full stop. Reserve written rules for judgment calls.
5. **Prune.** Find rules and skills that change nothing, rules the code now contradicts, and checks that never fire. Read the previous retro report and say whether its accepted proposals stopped the corrections.

## Output

Write the report to `~/.local/state/kitchen/retro/<yyyy-mm-dd>.md` and summarize it in the reply.

| # | Problem | Evidence (count, one quote, session) | Layer | Concrete change (file and text or test) | Cost |
|---|---|---|---|---|---|

Then a **Prune** list and a **Last retro** check. Never apply a change; each one waits for my approval.
