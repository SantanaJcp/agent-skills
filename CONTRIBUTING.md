# Contributing

Contributions are welcome through curated pull requests. The maintainer retains final approval and stable-promotion authority.

## Before contributing

1. Read the authoring, testing, compatibility, architecture, and security guides.
2. Discuss substantial policy or architecture changes before implementation.
3. Create new skills with `npm run new:skill -- <name>`.
4. Never import a personal skill directory or include private operational data.
5. For Acta changes, edit canonical sources and run `npm run acta`; never hand-edit materialized copies.

## Skill lifecycle

Every new skill begins in the incubator. An incubator change provides portable metadata, auditable content, trigger/non-trigger cases, and passing deterministic checks.

The initial fifteen Acta skills are one promotion cohort. None can be promoted until the versioned suite report records complete Codex/Claude, core-cycle, browser, and accessibility evidence. Later skills use the normal separate reviewed promotion process unless another ADR establishes a cohort.

A stable promotion records current client versions, observed activation results, optional-sidecar independence, isolated installation, network review, provenance, and security review. Fundamentally client-specific skills remain incubating.

## Checks

```bash
npm ci
npm run acta
npm run catalog
npm run check
```

Do not edit generated catalogs or materialized Acta references directly.

## Pull requests

- Keep each pull request focused on one coherent slice.
- Use an English title and description suitable for squash history and release notes.
- Complete the deterministic checklist and attach manual evidence only when promoting.
- Confirm descriptions distinguish neighboring skills and that sidecars remain presentation-only.
- Do not include model credentials or expect public CI to run paid model evaluations.

## Licensing

The repository uses Apache-2.0 under inbound-equals-outbound terms without a CLA or DCO. Contributors must have the right to submit every instruction, source, example, and asset.
