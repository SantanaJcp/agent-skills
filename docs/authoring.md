# Authoring Skills

## Create

```bash
npm run new:skill -- concise-kebab-name
```

Every new skill begins in the incubator with a matching smoke definition. Replace every `TODO` before review.

## Portable frontmatter

Required fields are `name`, a trigger-rich `description`, `license: Apache-2.0`, and comma-separated `metadata.tags`. Optional `compatibility` describes concrete environment requirements. Stable behavior cannot depend on client-only frontmatter.

Descriptions must lead with the action, cover each genuine trigger branch once, and distinguish adjacent non-triggers. Installing the whole suite makes description collision quality load-bearing.

## Information hierarchy

Keep ordered behavior and checkable completion criteria in `SKILL.md`. Put optional detail in shallow files directly linked from `SKILL.md`:

- `references/` for supporting protocol and HTML scaffolds;
- `scripts/` for portable `.mjs` automation using Node built-ins or bundled relative modules;
- `assets/` only for necessary licensed media with complete notices;
- `agents/openai.yaml` for optional presentation metadata.

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

When `agents/openai.yaml` exists, it is presentation-only and contains an interface display name, a 25–64-character short description, and a one-sentence default prompt mentioning `$skill-name`. Sidecars cannot declare required dependencies or invocation policy. Icons and brand colors are omitted from the initial suite.

## Restrictions

No symlinks, opaque executables, generated secrets, hidden install-time actions, runtime package imports, child-process execution, personal/private operational data, or undeclared external tools. Network code requires explicit maintainer review.

## Promote

Promotion is a separate reviewed change. The initial Acta cohort was promoted
under the explicit browser/accessibility waiver recorded in ADR 0005; that
historical exception does not silently relax later promotion requirements. Run
`npm run check`, isolated installation, and the applicable versioned manual
matrix before promotion, or record any waiver in a reviewed ADR and public
tracking issue.
