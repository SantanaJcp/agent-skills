---
name: what-just-happened
description: "Create an evidence-backed incident record and postmortem timeline without directing active mitigation or inventing owners. Use during an incident to capture a draft or after stabilization to complete the report; do not use as the debugging or incident-command process."
license: Apache-2.0
metadata:
  tags: "incident, postmortem, operations"
---

# What Just Happened

## Purpose

Preserve what happened, its evidence, impact, cause state, and real follow-up ownership. During an active incident this skill documents only; it does not direct response.

Read [the Acta v2 protocol](references/acta2-protocol.md). The postmortem is a **record-only** artifact — no fake active-incident controls, no invented owners. Write `scenario.json` (impact facts, an epistemically typed timeline of fact/hypothesis/mitigation/recovery entries, root cause, contributing conditions, follow-ups) and, after the report is reviewed and accepted in chat, `canonical.json`; generate the record with [the bundled generator](references/acta2/generate-record.mjs). [record.html](references/record.html) is a rendered example. The Acta 0.1 recipe ([acta-protocol.md](references/acta-protocol.md), [acta-scaffold.html](references/acta-scaffold.html)) remains bundled as the published compatibility fallback; Acta v2 is authoritative.

## Process

1. Determine whether the incident is active or stabilized. Create `incident-report.md` and optionally `timeline.json`; event timestamps are permitted because time is part of the incident fact.
2. During an active incident, capture sourced observations, commands/events, decision times, impact evidence, and mitigation state. Mark hypotheses as hypotheses. Keep status draft and do not assign actions or claim root cause.
3. After stabilization, reconcile the timeline against logs, monitoring, deploys, diffs, tickets, and participant accounts. Separate detection, impact, mitigation, recovery, and follow-up.
4. State root cause only when validated; otherwise state the strongest evidence and remaining owner. Include hypotheses considered, contributing conditions, and what evidence falsified alternatives.
5. Quantify impact with a basis. Record action owners and dates only when real; use “owner pending” visibly rather than inventing responsibility.
6. Generate `view.html` with the one permitted inverse TL;DR, semantic timeline, evidence blocks, impact table, and disclosures. Complete only after stabilization and evidence review.

## Guardrails

- Do not coordinate mitigation, page people, assign owners, or modify production.
- Do not turn temporal correlation into root cause.
- Preserve uncertainty and disputed accounts explicitly.
