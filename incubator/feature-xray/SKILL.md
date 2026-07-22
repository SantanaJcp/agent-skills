---
name: feature-xray
description: "Explain how an existing feature actually works through source-located evidence, operational flow, gotchas, and an Acta record. Use when someone needs a codebase-grounded feature walkthrough; do not use for general concept teaching or proposed implementation design."
license: Apache-2.0
metadata:
  tags: "codebase, explanation, documentation"
---

# Feature X-Ray

## Purpose

Produce a verifiable operational explanation of an existing feature without modifying it.

Read [the Acta artifact protocol](references/acta-protocol.md) and use [the Document scaffold](references/acta-scaffold.html).

## Process

1. Define the feature boundary, audience, and questions. Read project domain context and ADRs before tracing code.
2. Follow the feature from entry point through domain modules, state/data changes, external adapters, failure/recovery, and observable output. Prefer runtime/tests/logs as corroboration when available.
3. Write `feature-xray.md`. Every load-bearing claim receives Fact or Inference, a repository-relative file:line location, and an evidence register id. Keep snippets minimal and decision-relevant.
4. Add a TL;DR, operational timeline, data flow, important invariants, security/permission behavior, failure paths, gotchas, and FAQ disclosures. Do not invent behavior that source evidence cannot support.
5. Generate `view.html`, verify all locations and links, and mark complete when every claim is labeled and locatable.

## Guardrails

- Do not propose a redesign unless the user separately asks; explanation is the product.
- Use trusted external docs only when dependency behavior cannot be established locally and label the source.
- Do not modify code or expose secret values in snippets.
