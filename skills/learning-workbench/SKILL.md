---
name: learning-workbench
description: "Maintain a durable, source-grounded learning workspace with mission, lessons, retrieval practice, records, and spaced review for any topic. Use for multi-session learning; do not use for a one-off concept model or a post-change understanding quiz."
license: Apache-2.0
metadata:
  tags: "learning, teaching, research"
---

# Learning Workbench

## Purpose

Support durable learning across sessions for any topic through trusted knowledge, relevant practice, retrieval, spacing, and explicit learning records.

Read [the Acta v2 protocol](references/acta2-protocol.md). Artifacts are **generated from structured JSON, never hand-edited**: write `scenario.json` (mission, waypoint lessons with sourced facts and model flows, retrieval-practice questions) and run [the bundled generator](references/acta2/generate-instrument.mjs); after the session export is confirmed in chat, `canonical.json` + [the record generator](references/acta2/generate-record.mjs) emit the session's durable learning record. The Acta 0.1 recipe ([acta-protocol.md](references/acta-protocol.md), [acta-scaffold.html](references/acta-scaffold.html)) remains only as rollback until the v2 migration is approved. This skill uses a user-selected durable workspace rather than `.agent-work`.

## Workspace

Use the current directory when it already contains a learning workspace; otherwise ask the user to choose one. Maintain:

- `MISSION.md` — why the topic matters and the outcomes the learner wants.
- `RESOURCES.md` — high-trust sources with relevance and quality notes.
- `NOTES.md` — teaching preferences and working observations.
- `learning-records/NNNN-name.md` — durable non-obvious lessons and mission changes.
- `lessons/NNNN-name.html` — self-contained Acta lessons.
- `reference/` — compressed printable reference documents.
- `practice.json` — structured attempts and real next-review dates.

## Process

1. Establish or revisit the mission. Confirm before changing it and record a material change in a new learning record.
2. Research high-quality primary sources. Never base load-bearing teaching solely on parametric memory. Update the resource register before teaching unsupported claims.
3. Estimate the learner's zone of proximal development from mission, records, and practice. Choose one tightly scoped lesson with one tangible win.
4. Write the canonical lesson record, then generate a short self-contained Acta HTML lesson with waypoints, cited knowledge, one practice loop, retrieval feedback, and static no-JS content.
5. Separate fluency from storage strength. Use desirable difficulty for practice, comparable answer formatting, spacing, and interleaving only where useful. Record the real attempt and next-review date.
6. Update references with compressed reusable knowledge and add a learning record only for durable insights. Recommend a trustworthy community when the learner needs real-world wisdom, while respecting a preference not to join one.
7. Complete a lesson when practice was attempted, state was exported, the next review is recorded, and the next lesson can be chosen from evidence.

## Guardrails

- Do not turn every interaction into a large course; keep lessons small.
- Do not duplicate detailed knowledge across lessons, references, and records.
- Use concept-lab for a one-off manipulable explanation and do-i-understand-this for one completed code change.
