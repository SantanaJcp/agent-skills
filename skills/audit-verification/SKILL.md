---
name: audit-verification
description: "Periodic check that a project's verify-<repo> skill still tells the truth: the feature map matches the code, every feature is driven live, and the verifier can still fail. Ends clean, changed, findings or blocked. Use when I ask to audit verification, or from the weekly automation."
disable-model-invocation: true
---

# audit-verification

A feature map starts to rot the moment the app changes, and a verifier that cannot fail is worse than none.

## Outcomes

Say which one:

- **clean**: every feature covered from source and live; nothing to change.
- **changed**: one PR with proven corrections to the verify skill.
- **findings**: the audit found drift or gaps, but fixing them was not authorized; report them with evidence and change nothing.
- **blocked**: coverage could not finish or a fix could not ship safely; say exactly why.

## Edit scope

Only the verify skill's own folder, and only when fixes are authorized; otherwise the outcome is **findings**. Never product code. When the map describes behavior the app no longer has, it is either doc drift (fix the map) or a product regression (report it; never edit the map to hide it).

## Three things to keep apart

- **Inventory**: what the map says exists (features, routes, entry points).
- **Drives**: what the verifier actually exercises live, and how.
- **Assertions**: what it checks after each drive, and whether that check can go red.

A feature can be in the inventory, driven, and still asserted by nothing. Report the three separately.

## Pass

0. **Locate** `.agents/skills/verify-*/`. None: stop and point to the template in this repo's `templates/verify/`. State the audited profile: environment, build or commit SHA, data set, account or role, and which verifier commands or flags. Every result below holds only for that profile.
1. **Inventory**: the map's README against its files; fix missing, extra or dead entries. For each feature file, compare entry points and routes with the code and cite drift with `file:line`. Sweep recent churn (`git log --since=<last audit>`) for user-facing surfaces missing from the map; require a concrete path before calling one missing.
2. **Drives**: run the full proof; every feature is exercised at least once. Run the doctor before the first drive and after any failure. A feature is "unreachable" only with the concrete prerequisite and the route attempted.
3. **Assertions**: for each feature, name the check that decides pass or fail. A drive whose only check is "no error" or "exit 0" is a gap.
4. **Can it fail?** In a scratch copy, run both controls for at least one or two features:
   - **negative control**: break one expectation or inject a known fault; the verifier must go red, on that assertion. At least one negative control must nullify the execution or its effect (skip the drive, stub the action to a no-op, drop the write), not only change an expected value: a verifier that never checks the effect stays green when nothing happened;
   - **positive control**: the unbroken copy, same command; it must be green.
   Red on both, or green on both, means the verifier is not measuring the feature. If it stays green under the fault, that is the most important finding of the audit.
5. **Triage**: doc drift, fix it; harness gap, fix it and drive it again; product gap, report it outside the PR. Without authorization to fix, all of them are findings.
   Never turn a known product defect into a green expectation. If the verifier must keep running past it, mark it as an explicit expected failure (XFAIL) that stays visible in every run and goes red the day it starts passing, with the defect's reference.

## Reply

Outcome; audited profile; inventory drift (fixed or found); features driven and unreachable ones with their prerequisite; features without a real assertion; product gaps and any XFAIL added; and each control run: command, expected, actual.

Principles (the kitchen's PRINCIPLES.md): `prove`, `truthful-state`.
