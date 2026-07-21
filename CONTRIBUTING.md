# Contributing

Contributions are welcome through curated pull requests. The maintainer retains final approval and stable-promotion authority.

## Before contributing

1. Read the authoring, testing, compatibility, and security guides.
2. Discuss substantial policy or architecture changes before implementation.
3. Create new skills with `npm run new:skill -- <name>`.
4. Never import a personal skill directory or include client, employer, or private operational data.

## Skill lifecycle

Every new skill begins in the incubator. An incubator pull request must provide valid metadata, auditable content, a trigger case, a non-trigger case, and passing deterministic checks.

Promotion is a separate pull request that moves the skill into the stable collection. It must additionally record:

- current Codex and Claude Code versions;
- observed trigger and non-trigger results in both clients;
- confirmation that optional sidecars are nonessential;
- confirmation that direct installation is self-contained;
- review of network behavior, third-party material, and security-sensitive instructions.

Fundamentally client-specific skills remain incubating.

## Checks

```bash
npm ci
npm run catalog
npm run check
```

The root check is the same acceptance seam used by CI. Do not edit generated catalogs directly.

## Pull requests

- Keep each pull request focused on one coherent change.
- Use an English title and description suitable for squash-merge history and release notes.
- Complete the pull-request checklist and attach manual evidence when promoting a skill.
- Do not include model credentials or expect public CI to run paid model evaluations.

## Licensing

The repository uses Apache-2.0. By submitting a contribution, you agree that your contribution is licensed under the same terms and confirm that you have the right to submit its instructions, source, examples, and assets. No CLA or DCO sign-off is required.
