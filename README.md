# agent-skills

A curated, Apache-2.0 library of self-contained [Agent Skills](https://agentskills.io/) for current stable Codex and Claude Code.

> **Pre-release:** the repository foundation is available, but no skill has been promoted and no public release has been published.

## Install

The primary distribution interface is [`npx skills add`](https://github.com/vercel-labs/skills). Global installation is shown first because this collection is intended for reuse across projects.

Select skills interactively and install them for both supported clients:

```bash
npx skills add SantanaJcp/agent-skills -g --agent codex claude-code
```

Install the complete collection globally without interactive skill selection:

```bash
npx skills add SantanaJcp/agent-skills --skill "*" -g --agent codex claude-code
```

Install one named skill:

```bash
npx skills add SantanaJcp/agent-skills@<skill-name> -g --agent codex claude-code
```

For a project-local installation, omit `-g`. A consuming project may commit its generated `skills-lock.json`; this publisher repository does not.

For a reviewed, reproducible CLI version, replace `npx skills` with `npx skills@1.5.19`. Avoid `-y` until you have inspected the skill and scripts. CLI audit results are advisory rather than a security guarantee. Set `DO_NOT_TRACK=1` or `DISABLE_TELEMETRY=1` to disable install telemetry.

## Browse

- [Stable catalog](CATALOG.md)
- [Incubator](INCUBATOR.md)

Stable skills pass the portable-format, security, deterministic, and manual Codex/Claude promotion gates. Incubator skills are experiments and carry no stable compatibility promise.

## Author

Requirements: Node `>=22.20.0` and npm.

```bash
npm ci
npm run new:skill -- my-skill
npm run check
```

The generator creates the skill in the incubator and a matching trigger/non-trigger smoke-case definition. Fill every placeholder before submitting a pull request.

Read the [authoring guide](docs/authoring.md), [testing guide](docs/testing.md), and [contribution guide](CONTRIBUTING.md) before promotion.

## Architecture

The repository intentionally publishes portable skill directories rather than native plugins. `npx skills add` installs skill folders; it does not install plugin hooks, MCP servers, agents, or lifecycle behavior. Native plugin manifests can be added later without moving the canonical collection if those capabilities become necessary.

See [architecture](docs/architecture.md) and [compatibility](docs/compatibility.md) for the detailed model.

## Security

Skills execute with the permissions of the client that invokes them. Review instructions, scripts, assets, and updates before use. See [SECURITY.md](SECURITY.md) for the reporting policy and repository safety guarantees.

## Publication status

The repository is published from the personal `SantanaJcp` account with these safeguards:

- protected `main` with pull requests and required Linux/Windows CI;
- squash merges only, with a maintainer emergency bypass;
- private vulnerability reporting enabled.

After the first real skill is public, add the documented skills.sh badge and verify the public owner/repository listing without promising an indexing deadline.

The first public release will be `v1.0.0` when the maintainer judges the collection and governance mature.
