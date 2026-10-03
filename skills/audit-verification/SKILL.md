---
name: audit-verification
description: "Periodic check that a project's verify-<repo> skill still tells the truth: the feature map matches the code, every feature is driven live, and the verifier can still fail. Ends clean, changed or blocked. Use when I ask to audit verification, or from the weekly automation."
disable-model-invocation: true
---

# audit-verification

A feature map starts to rot the moment the app changes, and a verifier that cannot fail is worse than none.

## Outcomes

Say which one:

- **clean**: every feature covered from source and live; nothing to change.
- **changed**: one PR with proven corrections to the verify skill.
- **blocked**: coverage could not finish or a fix could not ship safely; say exactly why.

## Edit scope

Only the verify skill's own folder. Never product code. When the map describes behavior the app no longer has, it is either doc drift (fix the map) or a product regression (report it; never edit the map to hide it).

## Pass

0. **Locate** `.agents/skills/verify-*/`. None: stop and point to the template in this repo's `templates/verify/`.
1. **Index**: the map's README against its files; fix missing, extra or dead entries.
2. **Source**: for each feature file, compare entry points and routes with the code and cite drift with `file:line`. Sweep recent churn (`git log --since=<last audit>`) for user-facing surfaces missing from the map; require a concrete path before calling one missing.
3. **Live**: run the full proof; every feature is exercised at least once. Run the doctor before the first drive and after any failure. A feature is "unreachable" only with the concrete prerequisite and the route attempted.
4. **Can it fail?** In a scratch copy, break one or two expectations or inject a known fault. The verifier must go red. If it stays green, that is the most important finding of the audit.
5. **Triage**: doc drift, fix it; harness gap, fix it and drive it again; product gap, report it outside the PR.

## Reply

Outcome, features covered, unreachable features with their prerequisite, drift fixed, product gaps found, and the result of each fault-injection check.
