# ADR 0002: Materialize one Acta development suite

- **Status:** Accepted
- **Date:** 2026-07-21

## Context

The publisher needs a coherent development workflow rather than unrelated skill prompts. Fifteen focused skills must share provenance, decisions, handoffs, and an offline visual language while remaining portable across Codex and Claude Code. The skills CLI installs a whole collection as separate skill directories, so a repository-root runtime dependency would break isolated installation and the existing portable-source decision.

## Decision

Publish exactly fifteen focused Agent Skills as a **bundle-first, standalone-capable** suite. Documentation recommends installing the whole collection, while every skill remains independently usable and has a precise implicit-invocation description. No router silently advances the cycle.

Adopt **Acta 0.1.0** as the publisher-owned, print-first design and artifact system. Canonical Acta sources live in publisher authoring infrastructure. A deterministic Node materializer copies the shared protocol into all fifteen bundles and a fully inline recipe scaffold into the fourteen HTML-producing bundles. Generated copies are never edited manually and installed skills never load publisher or sibling paths at runtime.

Canonical working state is Markdown plus JSON only when the state is genuinely structured. HTML is a regenerable offline interface that cannot write project files or persist hidden browser state. Human decisions and publication remain explicit.

All fifteen skills begin in the incubator and form one initial promotion cohort. None enters stable until individual Codex/Claude trials, the complete core-cycle trial in both clients, and the manual Acta browser/accessibility matrix pass.

## Consequences

- Shared installed files are duplicated by distribution but maintained from one source.
- Whole-bundle installation is the primary product path without weakening isolated installation.
- Fourteen skills gain a consistent HTML contract without a runtime renderer, watcher, server, package, or network dependency.
- `make-me-realize` stays text-only while still using the artifact protocol.
- Promotion is slower because the first cohort is validated jointly, but stable cannot expose a partial cycle.
- Codex presentation sidecars may improve discovery but remain nonessential to portable behavior.
