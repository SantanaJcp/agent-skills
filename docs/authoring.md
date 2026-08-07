# Authoring Skills

## Create

```bash
npm run new:skill -- concise-kebab-name
```

Every new skill begins in the incubator with a matching smoke definition. Replace every `TODO` before review.

## Portable frontmatter

Required fields are `name`, a clear `description`,
`disable-model-invocation: true`, `license: Apache-2.0`, and comma-separated
`metadata.tags`. Optional `compatibility` describes concrete environment
requirements. Client-specific frontmatter cannot contain task instructions.

Descriptions serve as marketplace and catalog copy for human selection. Lead
with the outcome a user receives, include recognizable request language, cover
each genuine use-case branch once, and distinguish the nearest alternative.
Descriptions never authorize implicit model invocation.

Keep publisher implementation details out of stable public skill copy. Product names, scaffold generations, materialization versions, migration history, and compatibility recipes belong in supporting references or maintainer tooling, not in the frontmatter description or `SKILL.md` narrative.

## Information hierarchy

Keep ordered behavior and checkable completion criteria in `SKILL.md`. Put optional detail in shallow files directly linked from `SKILL.md`:

- `references/` for supporting protocol and HTML scaffolds;
- `scripts/` for portable `.mjs` automation using Node built-ins or bundled relative modules;
- `assets/` only for necessary licensed media with complete notices;
- `agents/openai.yaml` for required Codex interface metadata and manual-invocation policy.

Supporting Markdown cannot chain to more Markdown. A skill never depends on a sibling or repository-root runtime file.

## Acta-backed skills

The canonical Acta source is publisher infrastructure. Edit canonical protocol, tokens, behavior, components, or recipes, then run:

```bash
npm run acta
npm run acta:check
npm run validate:acta
```

Never edit a materialized `references/acta-protocol.md` or `references/acta-scaffold.html` by hand. Fourteen suite skills receive a self-contained scaffold; the text-only realization skill receives only the protocol.

At runtime the agent uses the scaffold as a structural contract and generates `view.html` from canonical Markdown/JSON state. There is no runtime renderer, watcher, server, CDN, package, browser storage, or direct file-writing behavior.

## Codex sidecars

Every skill contains `agents/openai.yaml` with an interface display name, a
25–64-character short description, a one-sentence default prompt mentioning
`$skill-name`, and `policy.allow_implicit_invocation: false`. The sidecar cannot
declare task instructions or required dependencies. Icons and brand colors are
omitted from the initial suite.

## Restrictions

No symlinks, opaque executables, generated secrets, hidden install-time actions, runtime package imports, child-process execution, personal/private operational data, or undeclared external tools. Network code requires explicit maintainer review.

## Promote

Promotion is a separate reviewed change. The initial Acta cohort was promoted
under the explicit browser/accessibility waiver recorded in ADR 0005; that
historical exception does not silently relax later promotion requirements. Run
`npm run check`, isolated installation, and the applicable versioned manual
matrix before promotion, or record any waiver in a reviewed ADR and public
tracking issue.
