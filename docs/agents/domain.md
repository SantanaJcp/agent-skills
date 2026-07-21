# Domain Docs

## Before exploring

Read, when present:

- Root `CONTEXT.md`
- Root `CONTEXT-MAP.md` if the repository later becomes multi-context
- Relevant ADRs under `docs/adr/`

Missing domain files are not errors. Proceed silently until domain terminology or architectural decisions need to be recorded.

## Layout

This repository uses the single-context layout:

```text
/
├── CONTEXT.md
├── docs/adr/
├── skills/
└── incubator/
```

## Vocabulary

Use terminology defined in `CONTEXT.md`. Do not introduce synonyms that conflict with the glossary.

If required terminology is missing, reconsider whether a new term is needed or record the gap for domain modeling.

## ADR conflicts

Explicitly identify output that contradicts an existing ADR rather than silently overriding it.
