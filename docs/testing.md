# Testing

## Highest acceptance seam

```bash
npm run check
```

The command runs behavior tests, typechecking, repository validation, skill validation, Acta freshness and static contracts, catalog freshness, and isolated installation. CI invokes the same seam on Linux and Windows.

Tests observe public commands and installed files rather than private helpers. Expected results come from the repository contract and worked examples.

## Acta deterministic checks

CI is static-only and credential-free. It validates deterministic materialization, protocol equality, all fourteen recipe structures, offline resources, safe DOM behavior, no browser storage, native controls, no-script content, print/reduced-motion declarations, token and contrast contracts, sidecars, provenance checksums, and catalog/install behavior. It does not install browsers, Axe, or pixel-snapshot tooling.

Realistic recipe artifacts live in test fixtures, never installed bundles. Visual review uses component contracts and the immutable component sheet rather than golden screenshots.

## Smoke and collision definitions

Every skill has committed trigger and adjacent non-trigger cases. The initial suite also records cross-skill collision cases for discovery versus blueprinting, code versus interface alternatives, prototyping versus implementation, codebase explanation versus concept teaching, incidents versus diagnosis, architecture analysis versus implementation, and flow versus general SVG illustration.

Public CI validates definitions but does not call paid models. Promotion records manual results in current Codex and Claude Code.

## Initial suite promotion evidence

Before moving any initial skill to stable:

- run every committed trigger/non-trigger case in both clients;
- run the complete six-stage scenario in the public synthetic fixture in both clients;
- exercise all fourteen recipes in current Chrome;
- exercise representative Document, Compare, Explore, Edit artifacts and critical interactions in current Safari and Firefox;
- verify keyboard, 320px, actual 400% zoom, print/PDF, no-JS, reduced motion, VoiceOver, and NVDA.

Record exact versions and results in the versioned Acta suite QA report. Windows CI is blocking; real-Windows serif rendering is documented but not blocking.

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
