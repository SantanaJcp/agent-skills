# Contributing

Contributions are welcome through curated pull requests. The maintainer retains final approval and stable-promotion authority.

## Before contributing

1. Read the authoring, testing, compatibility, architecture, and security guides.
2. Discuss substantial policy or architecture changes before implementation.
3. Create new skills with `npm run new:skill -- <name>`.
4. Never import a personal skill directory or include private operational data.
5. For Acta 0.1 compatibility changes, edit its canonical sources and run `npm run acta`; for the authoritative Acta v2 system, edit `design/acta2/` and run `npm run acta2`. Never hand-edit materialized copies.

## Skill lifecycle

Every new skill begins in the incubator. An incubator change provides portable metadata, auditable content, trigger/non-trigger cases, and passing deterministic checks.

The initial fifteen Acta skills were promoted together in `v1.0.0` after the
client and core-cycle rows passed. ADR 0005 records the owner's one-time waiver
for the browser and accessibility rows; [GitHub Issue #8](https://github.com/SantanaJcp/agent-skills/issues/8)
tracks that deferred work without treating it as passed. Later skills use the
normal separate reviewed promotion process unless another ADR establishes a
cohort.

A stable promotion records current client versions, observed activation results, optional-sidecar independence, isolated installation, network review, provenance, and security review. Fundamentally client-specific skills remain incubating.

## Checks

```bash
npm ci
npm run acta
npm run catalog
npm run check
```

Do not edit generated catalogs or materialized Acta references directly.

## Manual QA contributions

Manual evaluators may contribute through a fork or a dedicated `qa/<surface>-<reviewer>` branch; repository write access is not required. Prepare the isolated harness with `npm run qa:prepare -- --destination <directory>`, follow `docs/qa/evaluator-runbook.md`, and copy `docs/qa/evidence/template.md` into one reviewer-owned evidence file. Do not edit the central suite verdict unless assigned as evidence integrator.

Record exact source and tool versions. Preserve failures against their original revision, keep fixes in separate changes, and rerun affected evidence after a fix. Never include private repositories, credentials, or production data.

## Pull requests

- Keep each pull request focused on one coherent slice.
- Use an English title and description suitable for squash history and release notes.
- Complete the deterministic checklist and attach manual evidence only when promoting.
- Confirm descriptions distinguish neighboring skills and that sidecars remain presentation-only.
- Do not include model credentials or expect public CI to run paid model evaluations.

## Licensing

The repository uses Apache-2.0 under inbound-equals-outbound terms without a CLA or DCO. Contributors must have the right to submit every instruction, source, example, and asset.
