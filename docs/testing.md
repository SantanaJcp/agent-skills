# Testing

## Highest acceptance seam

```bash
npm run check
```

The command runs behavior tests, typechecking, repository validation, skill
validation, Acta freshness and static contracts, catalog freshness, whole-suite
installation, every standalone skill installation, and installed Acta v2
generator execution. CI invokes the same seam on Linux and Windows.

Tests observe public commands and installed files rather than private helpers. Expected results come from the repository contract and worked examples.

## Acta deterministic checks

CI is static-only and credential-free. It validates deterministic materialization, protocol equality, all 14 Acta v2 bundles and their 26 instrument/record fixtures, offline resources, safe DOM behavior, no browser storage, native controls, no-script content, print/reduced-motion declarations, token and contrast contracts, sidecars, provenance checksums, and catalog/install behavior. It does not install browsers, Axe, or pixel-snapshot tooling.

On a host where an installed Chromium binary cannot start, set
`ACTA2_SKIP_BROWSER_PROBES=1` to run the deterministic seam while marking the
four opportunistic Chromium probes skipped. This is an honest test-environment
control, not browser evidence and not closure of
[GitHub Issue #8](https://github.com/SantanaJcp/agent-skills/issues/8).

Realistic recipe artifacts live in test fixtures, never installed bundles. Visual review uses component contracts and the immutable component sheet rather than golden screenshots.

## Smoke and collision definitions

Every skill has committed trigger and adjacent non-trigger cases. The initial suite also records cross-skill collision cases for discovery versus blueprinting, code versus interface alternatives, prototyping versus implementation, codebase explanation versus concept teaching, incidents versus diagnosis, architecture analysis versus implementation, and flow versus general SVG illustration.

Public CI validates definitions but does not call paid models. Promotion records manual results in current Codex and Claude Code.

## Reproducible manual harnesses

`npm run qa:prepare -- --destination <outside-repository-directory>` copies the public synthetic project, smoke/collision cases, fourteen browser fixtures, and all fifteen stable bundles into isolated `with-sidecars` and `without-sidecars` project roots. The command refuses dirty default sources and existing destinations, then stamps each harness with the full source revision. It does not modify global client installations.

Reviewers follow `docs/qa/evaluator-runbook.md` and submit separate sanitized
summary files from `docs/qa/evidence/template.md`; raw logs and captures remain
outside the repository. A central integrator owns the suite verdict so parallel
reviewers do not overwrite one another.

## Published initial-suite promotion record

The `v1.0.0` promotion plan assigned the following manual matrix:

- run every committed trigger/non-trigger case in both clients;
- run the complete six-stage scenario in the public synthetic fixture in both clients;
- exercise all 13 instruments and 13 records in current Chrome;
- exercise every interactive Acta v2 kind, a representative record, and critical interactions in current Safari and Firefox;
- verify keyboard, 320px, actual 400% zoom, print/PDF, no-JS, reduced motion, VoiceOver, and NVDA.

The client and core-cycle portions passed. Browser and assistive-technology rows
were explicitly deferred, not passed; ADR 0005 records the one-time waiver and
[GitHub Issue #8](https://github.com/SantanaJcp/agent-skills/issues/8) tracks the
remaining matrix. Windows CI was blocking and passed; real-Windows serif
rendering remains documented but nonblocking.

## Focused commands

```bash
npm test
npm run typecheck
npm run acta:check
npm run validate:acta
npm run validate
npm run catalog:check
npm run test:install
```
