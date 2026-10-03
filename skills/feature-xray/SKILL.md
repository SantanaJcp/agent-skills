---
name: feature-xray
description: "Read-only investigation of an area (feature, folder, service, branch, deployment) that ends in numbered decisions, never in changes. Use when I say 'analiza', 'primero analicemos', 'qué hace X hoy', 'no cambies nada', or before proposing changes to code you have not read."
---

# feature-xray

Explain how something works today, from evidence, and hand me the decisions. The x-ray ends at decisions; it never fixes anything.

## Read-only, strictly

No edits, commits, branch changes, installs, migrations, deploys or deletions. Run only commands that read: `git log`, `grep`, builds and tests that touch no shared state, the project's verify skill in its read-only commands. If answering needs a mutating step, stop and ask.

## Steps

1. **Scope.** State the area, the question it answers, and what is out of scope.
2. **Map from source.** Entry points, data flow, callers, configuration, tests. Cite `file:line`.
3. **Churn.** `git log --since=60.days --stat -- <path>`: what changes often, who touched it last, which large files change the most (size × commits).
4. **Check against reality** when it is cheap: run the tests or the verify command that covers it. Label each claim measured, inferred or guess.
5. **Look for** dead or orphaned pieces, docs or comments that contradict the code, existing fallbacks (report them per the global rules), and risks.

## Output

- **In short**: one paragraph, what it is and your verdict.
- **Map**: table of component → role → `file:line`.
- **Findings**: each with its evidence label and location, worst first.
- **Decisions**: numbered, each with your recommended option, its cost, and whether it is a one-way or two-way door.
