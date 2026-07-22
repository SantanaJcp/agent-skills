# agent-skills

A bundle-first, Apache-2.0 development system of fifteen portable [Agent Skills](https://agentskills.io/) for current stable Codex and Claude Code.

> **Pre-release:** all fifteen skills are incubating. None carries the stable compatibility promise until the complete suite passes the joint client, browser, and accessibility gates.

## Install the complete suite

The recommended experience installs the whole development cycle and its autonomous tools globally for both supported clients:

```bash
npx skills add SantanaJcp/agent-skills --skill '*' -g --agent codex claude-code
```

For a reviewed, reproducible CLI version, use `npx skills@1.5.19`. Avoid `-y` until you have inspected the skills and scripts. Set `DO_NOT_TRACK=1` or `DISABLE_TELEMETRY=1` to disable install telemetry.

Advanced consumers may select skills interactively:

```bash
npx skills add SantanaJcp/agent-skills -g --agent codex claude-code
```

Or install one self-contained skill:

```bash
npx skills add SantanaJcp/agent-skills@<skill-name> -g --agent codex claude-code
```

For a project-local installation, omit `-g`. A consumer may commit its generated `skills-lock.json`; this publisher does not.

## Development cycle

1. `make-me-realize` — expose blind spots and own every unknown.
2. `three-code-paths` — compare three structural implementation choices.
3. `interface-directions` — conditionally choose a product-interface direction.
4. `change-blueprint` — approve a compact spec and implementation plan.
5. `build-with-notes` — implement test-first with live notes and STOP gates.
6. `do-i-understand-this` — diagnose understanding of the completed change.

The bundle also includes `feel-the-flow`, `feature-xray`, `concept-lab`, `what-just-happened`, `draw-the-flow`, `draw-it-in-svg`, `deepen-the-codebase`, `find-the-cause`, and `learning-workbench`.

Skills may recommend a handoff, but never invoke the next stage automatically. Markdown/JSON is canonical; Acta HTML is an offline, printable human interface.

## Browse

- [Stable catalog](CATALOG.md)
- [Incubator](INCUBATOR.md)
- [Acta architecture](docs/architecture.md)
- [Acta promotion evidence](docs/qa/acta-suite-0.1.0.md)

## Author

Requirements: Node `>=22.20.0` and npm.

```bash
npm ci
npm run new:skill -- my-skill
npm run acta
npm run catalog
npm run check
# For assigned manual evaluation:
npm run qa:prepare -- --destination ../agent-skills-manual-qa
```

Acta authoring sources are publisher-only. Materialized protocol and HTML scaffolds are committed inside skill bundles so whole-collection and isolated installs work without network, runtime packages, sibling skills, renderers, watchers, or servers.

Read the [authoring guide](docs/authoring.md), [testing guide](docs/testing.md), and [contribution guide](CONTRIBUTING.md) before promotion.

## Security

Skills execute with the invoking client's permissions. Review instructions, scripts, artifacts, and updates before use. HTML views do not write canonical files or persist browser storage. See [SECURITY.md](SECURITY.md).

## Publication status

The repository is published from the personal `SantanaJcp` account with protected `main`, required Linux/Windows CI, squash merges, a maintainer emergency bypass, and private vulnerability reporting.

The first public release will be `v1.0.0` only after the fifteen-skill cohort is promoted. This repository prepares but does not automatically dispatch that release.
