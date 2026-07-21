# Authoring Skills

## Create

```bash
npm run new:skill -- concise-kebab-name
```

The command rejects invalid names, duplicate stable/incubator names, and existing smoke-case files. It creates an incubator skill plus a matching smoke definition. Replace every `TODO` before opening a pull request.

## Portable frontmatter

Required fields:

- `name` — 1–64 lowercase letters, digits, and single hyphens; equal to the directory name.
- `description` — 1–1024 characters describing what the skill does and explicitly using `when` to state its activation context.
- `license` — `Apache-2.0`.
- `metadata.tags` — a comma-separated string of topical kebab-case tags.

Optional `compatibility` may describe a concrete environment requirement in at most 500 characters. Stable skills must not use client-only behavioral frontmatter.

## Bundle

Keep `SKILL.md` concise and put optional resources in conventional directories:

- `scripts/` for `.mjs` Node standard-library automation;
- `references/` for supporting documents linked directly from `SKILL.md`; supporting Markdown must not chain to more Markdown;
- `assets/` for necessary licensed media, accompanied by a root `THIRD_PARTY_NOTICES.md` that records provenance and license for every asset;
- `agents/openai.yaml` for optional nonessential Codex presentation metadata;
- `THIRD_PARTY_NOTICES.md` for asset provenance; original assets identify the project as creator and Apache-2.0, while third-party entries include source, copyright holder, and compatible license.

References must be relative, resolve, and stay inside the skill. Do not depend on sibling skills or repository-root runtime files.

## Restrictions

- No external runtime tools or package installation.
- No symlinks, generated secrets, opaque executables, or hidden install-time actions.
- No runtime package imports or child-process execution.
- Network code requires explicit maintainer review.
- No personal, employer, client, or private operational data.

## Promote

Promotion is a separate reviewed change. Complete the smoke evidence described in the testing guide, verify direct installation, regenerate catalogs, and run `npm run check`.
