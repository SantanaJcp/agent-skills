# Spec: Agent Skills Repository Foundation

Status: ready-for-agent

## Problem Statement

The repository intended to hold and share custom agent skills is currently an almost blank Git repository. It has no stable skill layout, authoring workflow, portable skill contract, validation tooling, catalog, contribution policy, security policy, release process, or public installation guidance. Without a deliberate foundation, skills could become coupled to one runtime, accidentally import private personal content, rely on undeclared tools, expose unsafe executable behavior, drift from their catalogs, or be difficult for other people to install and trust.

The maintainer needs a curated public-library foundation that is useful for personal authoring while teaching other users how the Agent Skills ecosystem works. Skills must be independently installable through `npx skills add`, work in both Codex and Claude Code, and move through a clear incubator-to-stable lifecycle. The repository must start without importing or publishing any existing personal skill.

## Solution

Build the foundation of a public GitHub repository named `agent-skills`, initially owned by the maintainer's personal account and licensed under Apache-2.0. The repository will use a flat stable collection and a separate flat incubator collection. Every new skill will be created in the incubator by a repository generator and promoted only after portable-format validation, deterministic checks, documentation review, and recorded Codex and Claude Code trigger and non-trigger trials.

Each published skill will be a self-contained Agent Skills unit with one canonical portable `SKILL.md`. Optional resources, Node standard-library scripts, licensed assets, and nonessential runtime presentation sidecars may accompany it. Every stable skill must function in both supported clients without relying on a sidecar, sibling skill, repository-level runtime file, external package, or externally installed tool.

The repository will provide pinned Node-based authoring tooling, generated stable and incubator catalogs, GitHub Actions, contribution and security policies, architecture documentation, and a manual semantic-release workflow. `npx skills add` will be the primary distribution path, with global installation documented first and project installation documented second. Native Codex and Claude plugin manifests will not be part of the initial foundation.

## User Stories

1. As the repository maintainer, I want a clear public-library identity, so that the project does not become an uncurated backup of personal skills.
2. As the repository maintainer, I want only skills deliberately created in this repository to be included, so that private personal skills are never imported automatically.
3. As a visitor, I want to understand the repository's purpose immediately, so that I can decide whether its skills are relevant to me.
4. As a visitor, I want the repository documentation to be canonically written in English, so that it is accessible to the broadest intended audience.
5. As a visitor, I want an architecture guide to the Agent Skills ecosystem, so that I can understand the relationships among portable skills, Codex, Claude Code, the skills CLI, and native plugins.
6. As a learner, I want temporary tooling differences and compatibility caveats explained, so that I do not mistake current client behavior for a timeless specification guarantee.
7. As a skill consumer, I want to browse a generated stable catalog, so that I can discover supported skills without reading every directory.
8. As a skill consumer, I want incubating skills listed separately, so that I do not mistake experiments for supported releases.
9. As a skill consumer, I want topical tags in catalog entries, so that I can find related skills while source storage remains flat.
10. As a skill consumer, I want to install the complete collection globally, so that the skills are available across my projects.
11. As a skill consumer, I want to install one named skill globally, so that I do not need to install unrelated skills.
12. As a project maintainer, I want to install selected skills locally to a project, so that the project controls its own reviewed agent capabilities.
13. As a Codex user, I want the documented install command to target Codex explicitly, so that the skill reaches the correct client location.
14. As a Claude Code user, I want the documented install command to target Claude Code explicitly, so that the same skill works in that client.
15. As a multi-client user, I want one install operation to support both clients, so that I do not maintain duplicate skill sources.
16. As a security-conscious consumer, I want installation instructions to avoid noninteractive confirmation by default, so that I can inspect what will be installed.
17. As a security-conscious consumer, I want to know that CLI audit results are advisory, so that I do not treat them as a security guarantee.
18. As a security-conscious consumer, I want instructions for pinning a reviewed skills CLI version, so that installation does not unexpectedly execute a different package release.
19. As a privacy-conscious consumer, I want CLI telemetry and its opt-out documented, so that I can make an informed choice.
20. As a project maintainer, I want consumer lock-file behavior explained, so that I know what should be committed in a consuming project and what does not belong in the publisher repository.
21. As a skill author, I want one command to scaffold a new skill, so that I begin with the repository's required conventions.
22. As a skill author, I want every generated skill to begin in the incubator, so that creation does not imply stability.
23. As a skill author, I want the generator to reject invalid or duplicate names, so that CLI discovery remains deterministic.
24. As a skill author, I want the generator to create smoke-test cases alongside the skill, so that behavioral intent is captured from the beginning.
25. As a skill author, I want optional resource directories created only when needed, so that each skill stays concise and understandable.
26. As a skill author, I want one canonical portable instruction document, so that Codex and Claude Code do not drift into separate implementations.
27. As a skill author, I want portable metadata rules documented and validated, so that my skill is compatible with the shared Agent Skills format.
28. As a skill author, I want the folder name and declared skill name to match, so that direct installation and cataloging are predictable.
29. As a skill author, I want skill names to be globally distinctive within the repository, so that CLI name deduplication never hides another skill.
30. As a skill author, I want descriptions to explain both capability and activation context, so that agents can select the skill correctly.
31. As a skill author, I want progressive disclosure through shallow references, so that the main instruction document remains focused.
32. As a skill author, I want standard locations for scripts, references, assets, and optional sidecars, so that skill bundles are easy to inspect.
33. As a skill author, I want a repository-wide Apache-2.0 license declaration in each independent skill's metadata, so that reuse rights remain clear after installation.
34. As a skill author, I want to use Node standard-library scripts when instructions alone are insufficient, so that automation remains cross-platform and dependency-free.
35. As a skill consumer, I want stable skill scripts to avoid runtime npm packages, so that installation does not trigger additional package setup.
36. As a skill consumer, I want stable and incubating skills to avoid externally installed tool dependencies, so that portability constraints are enforced from the start.
37. As a skill consumer, I want installed skills to be self-contained, so that a directly installed skill never breaks because repository siblings are absent.
38. As a skill consumer, I want skill bundles free of symlinks, generated secrets, and opaque executables, so that installed content is auditable.
39. As a skill consumer, I want third-party media to carry compatible licensing and attribution, so that installed assets can be reused lawfully.
40. As a security reviewer, I want network-capable scripts reviewed case by case, so that legitimate behavior is possible without hiding data flows.
41. As a Codex user, I want optional Codex presentation metadata to remain nonessential, so that the portable core still works elsewhere.
42. As a Claude Code user, I want stable skills to avoid Claude-only behavioral features, so that the shared compatibility promise remains true.
43. As a skill author, I want a fundamentally runtime-specific skill to remain incubating, so that stable status never overstates portability.
44. As a reviewer, I want every stable skill tested in current stable Codex and Claude Code versions, so that compatibility claims are evidence-based.
45. As a reviewer, I want recorded prompts that should trigger a skill, so that intended activation can be verified.
46. As a reviewer, I want recorded prompts that should not trigger a skill, so that overly broad activation can be detected.
47. As a reviewer, I want exact client versions recorded with manual smoke results, so that compatibility evidence has useful context.
48. As a contributor, I want deterministic checks to run without model credentials, so that public pull requests do not expose secrets or incur variable model costs.
49. As a contributor, I want one root acceptance command, so that I can reproduce the same checks that CI uses.
50. As a contributor, I want validation failures to explain the violated repository contract, so that I can correct my work without maintainer guesswork.
51. As a contributor, I want generated catalog drift detected automatically, so that metadata and published discovery pages stay synchronized.
52. As a contributor, I want clear pull-request templates for incubator additions and stable promotions, so that I provide the required evidence.
53. As an outside contributor, I want to submit improvements without signing a CLA or DCO, so that contribution remains low-friction.
54. As an outside contributor, I want contribution licensing explained as inbound-equals-outbound under Apache-2.0, so that rights and responsibilities are clear.
55. As a community participant, I want a standard code of conduct, so that expected behavior and enforcement are documented.
56. As a security reporter, I want a private GitHub reporting channel after publication, so that unsafe skill behavior is not disclosed first in a public issue.
57. As the maintainer, I want final approval over outside skills and promotions, so that the public collection remains curated.
58. As the maintainer, I want protected pull-request-based changes to the default branch, so that required checks cannot be bypassed accidentally.
59. As the maintainer, I want an emergency bypass, so that urgent repository or security corrections remain possible.
60. As the maintainer, I want squash merges, so that public history contains one intentional commit per accepted change.
61. As the release manager, I want repository-wide semantic versions, so that compatibility changes are communicated consistently.
62. As the release manager, I want one root changelog and matching GitHub release notes, so that users can understand each release from either surface.
63. As the release manager, I want releases started through a manual workflow, so that version selection and changelog preparation remain deliberate.
64. As the release manager, I want the first published release to be v1.0.0 only when the maintainer judges the repository mature, so that an empty scaffold is not presented as a usable collection.
65. As a skill consumer, I want a stable skill deprecated before removal, so that I have time and guidance to migrate.
66. As a skill consumer, I want stable skill removal restricted to a major release, so that semantic-version expectations are honored.
67. As a maintainer, I want a documented security exception to normal deprecation timing, so that actively unsafe content can be removed promptly.
68. As a compatibility maintainer, I want claims limited to current stable client versions, so that the project does not promise indefinite support for obsolete clients.
69. As a repository automation agent, I want concise root authoring instructions, so that generated changes follow the same layout, security, validation, and promotion rules as human contributions.
70. As an engineering agent, I want local specs to carry canonical triage status, so that fully synthesized work can be discovered as ready for implementation.
71. As a maintainer, I want the initial scaffold to contain a template but no discoverable example skill, so that the first published content is deliberate and useful.
72. As a future plugin maintainer, I want the canonical skill collection to remain reusable by native plugin manifests later, so that adding plugin capabilities does not require relocating or duplicating skills.
73. As a visitor, I want the skills.sh badge and listing verified after publication, so that I can discover the collection through the ecosystem directory.
74. As the maintainer, I want documentation to avoid promising a skills.sh indexing deadline, so that third-party directory behavior is represented accurately.
75. As the maintainer, I want repository authoring dependencies isolated from installed skill runtime dependencies, so that strong local tooling does not make individual skills heavier.
76. As a reviewer, I want repository tooling tested on Linux and Windows, so that cross-platform claims cover materially different environments.

## Implementation Decisions

- The product is a curated public library named `agent-skills`, designed for both personal use and independent public adoption.
- The canonical host will eventually be a public GitHub repository under the maintainer's personal account. Remote creation and administrative settings require a human publishing step.
- The project and independently installed skills use Apache-2.0. Contributions use inbound-equals-outbound licensing without a CLA or DCO sign-off requirement.
- English is the canonical language for skills, documentation, metadata, tests, and release notes. Translations may be added later but are not sources of truth.
- Published skills live in a flat stable collection. New and experimental skills live in a separate flat incubator collection on the default branch.
- Every new skill starts in the incubator. Stable promotion is an explicit move after all quality gates pass.
- Initial scaffolding includes an authoring template but no stable skill, incubating example, or imported personal skill.
- Only skills deliberately authored or contributed to this repository are eligible for inclusion. No tooling may scan or synchronize personal skill directories.
- Each skill is a self-contained directory with one canonical `SKILL.md`. Optional conventional resources include scripts, references, assets, and runtime presentation metadata.
- Skill names use lowercase kebab-case, are 1–64 characters, match their containing directory, contain no leading, trailing, or consecutive hyphens, and are unique across stable and incubator collections.
- Descriptions are 1–1024 characters and must explain both what the skill does and when it should be used.
- Portable frontmatter is the source of truth. The template includes the name, description, Apache-2.0 license, and a string-valued tag metadata field. Compatibility metadata is optional when it describes a concrete environment constraint.
- Experimental or client-specific frontmatter is not allowed in a stable portable core when it changes runtime behavior or breaks another supported client's validator.
- Every stable skill must function in current stable Codex and Claude Code versions. Runtime presentation sidecars may enhance appearance or discovery but cannot be required for correct behavior.
- Skills that fundamentally require runtime-only invocation controls, fork contexts, hooks, agents, or similar behavior remain incubating until an equivalent portable path exists.
- Skills cannot rely on sibling skills or repository-root runtime assets. Every referenced runtime resource must be contained inside the installed skill.
- Stable and incubating skill scripts use cross-platform Node modules with standard-library imports only. Runtime npm packages and externally installed command-line tools are forbidden.
- Repository authoring tooling may use exact, lockfile-pinned development dependencies because it is not copied into installed skills.
- Bundled content may include text, auditable source, and licensed media. Symlinks, generated secrets, and opaque executable binaries are forbidden.
- Third-party bundled material requires compatible licensing and local attribution that remains present when the skill is installed independently.
- Network behavior in source scripts is reviewed case by case. There is no blanket offline rule, but install-time network behavior and hidden side effects are forbidden.
- The shared Agent Skills format is the canonical source model. The initial repository does not maintain separate Codex and Claude skill variants.
- `npx skills add` is the primary installation interface. Documentation leads with global installation, then explains project-local installation and consumer lock-file handling.
- The initial distribution is CLI-first and contains no native Codex or Claude plugin manifests. Native manifests may be introduced later only for capabilities that the skills CLI does not install.
- The repository owns strict validation against its portable contract. The skills CLI's list operation is used only as a discovery smoke test, not as a complete validator.
- Repository tooling uses a private Node package with a committed lockfile. The Node engine floor matches the supported skills CLI floor, while CI initially runs on the current Node LTS line.
- The root command `npm run check` is the single highest automated acceptance seam. CI invokes the same command rather than reimplementing its behavior in workflow YAML.
- The acceptance command covers generator behavior, strict skill validation, security checks, generated-catalog freshness, tooling tests, CLI discovery, and temporary installation for both supported clients.
- Model-backed activation testing does not run in public CI. Promotion pull requests record manual Codex and Claude trigger and non-trigger evidence with tested client versions.
- Stable and incubator catalogs are generated from canonical skill metadata and committed for GitHub browsing. CI fails when generated output is stale.
- The catalog uses tags for topical views while source directories remain flat. Stable and incubator content are always presented separately.
- Documentation includes a quick start, architecture and ecosystem explanation, authoring guide, compatibility policy, testing guide, release guide, contribution guide, security policy, code of conduct, changelog, and concise agent instructions.
- The repository explains the difference among the Agent Skills specification, client discovery paths, `npx skills add`, native plugins, CLI telemetry, advisory audits, and consumer lock files.
- Public contributions are accepted through curated pull requests. The maintainer retains approval and promotion authority.
- The default branch requires pull requests and deterministic checks, with an emergency maintainer bypass. Accepted pull requests use squash merges.
- The Contributor Covenant is the community conduct policy. GitHub private vulnerability reporting is the security-reporting channel after the remote exists.
- Releases apply semantic versions to the collection as a whole. The project does not maintain independent per-skill release streams.
- A manual GitHub workflow validates the requested version, changelog, tested-client information, and acceptance checks before creating a tag and GitHub Release. It does not publish an npm package.
- The first public release is v1.0.0 when the maintainer judges content and governance mature. No fixed number of skills determines readiness.
- Backward-compatible fixes use patch releases; new compatible skills and deprecations use minor releases; repository-contract breaks and stable-skill removals use major releases.
- A stable skill is deprecated for at least one minor release with migration or replacement guidance before removal in a major release. An actively unsafe skill may use a documented security exception.
- Compatibility claims cover the current stable Codex, Claude Code, and skills CLI versions tested at promotion and release time. Obsolete clients receive no long-term support promise.
- skills.sh visibility is a post-publication verification goal. Documentation may include the official badge but must not guarantee deterministic indexing or an indexing deadline.
- Until the GitHub remote exists, engineering specs and implementation issues use the configured local Markdown tracker and canonical triage vocabulary.

## Testing Decisions

- A good test observes public repository behavior rather than private helper implementation. It should prove that an author can scaffold a valid skill, that invalid or unsafe skills are rejected with useful diagnostics, that catalogs represent canonical metadata, and that consumers can discover and install the resulting skill for both supported clients.
- The ideal automated test seam is one root command: `npm run check`. This is a new seam because the repository has no existing application or test runner.
- The acceptance seam must be runnable locally and in CI with the same behavior. Workflow configuration should orchestrate environments, not duplicate validation rules.
- Generator tests cover valid creation, invalid names, duplicate names across both maturity collections, refusal to overwrite existing work, and creation of the matching smoke-test case definition.
- Strict validation tests cover required frontmatter, portable allowed fields, name constraints, directory/name equality, description length, license metadata, string-valued tags, relative-link containment, shallow references, and unique names.
- Self-containment tests reject references outside a skill, reliance on sibling skills, missing bundled resources, and runtime imports from repository-level tooling.
- Script-policy tests allow Node standard-library and relative imports while rejecting runtime package imports and attempts to execute undeclared external tools.
- File-safety tests reject symlinks, suspicious secrets, opaque executable binaries, and unlicensed third-party material. Network-related standard-library imports produce an explicit review signal rather than an automatic blanket rejection.
- Catalog tests regenerate stable and incubator indexes from fixtures and verify deterministic ordering, tag grouping, maturity separation, descriptions, and installation examples.
- Discovery smoke tests exercise the pinned skills CLI against a synthetic repository fixture because the initial publisher repository intentionally contains no real skill.
- Installation acceptance tests use isolated temporary user and project homes. They verify Codex and Claude destinations, multi-client installation behavior, direct single-skill installation, whole-collection selection, and the absence of publisher lock-state pollution.
- Cross-platform CI runs the acceptance seam on Linux and Windows. Node tooling must not rely on shell-only behavior that breaks Windows.
- Release checks verify semantic-version syntax, matching changelog entries, tested-client version records, clean generated catalogs, passing acceptance checks, and absence of an existing tag.
- Promotion evidence remains partly manual: reviewers record at least representative trigger and non-trigger prompts and observed behavior in current Codex and Claude Code releases. No model API credentials are stored for pull-request CI.
- The promotion checklist verifies that optional runtime sidecars are nonessential and that a clean installation of the portable core works in both clients.
- Prior art comes from the public Agent Skills format, current Codex and Claude discovery behavior, and the official skills CLI's discovery and installation behavior. The current repository has no prior test suite to preserve.

## Out of Scope

- Importing, synchronizing, or publishing existing personal skills.
- Creating a stable or incubating example skill as part of the initial scaffold.
- Authoring the first real skill or deciding which skill should be published first.
- Publishing a v0.x release or automatically releasing the empty foundation.
- Creating the GitHub repository, selecting the final GitHub username placeholder, or applying remote administrative settings that require owner credentials.
- Migrating the configured local Markdown tracker to GitHub Issues.
- Native Codex or Claude plugin manifests, marketplaces, hooks, MCP dependencies, packaged agents, or plugin lifecycle behavior.
- Maintaining separate runtime-specific source variants.
- Promoting a skill that supports only one of the two required clients.
- Runtime npm packages, automatic dependency installation, or externally installed tool prerequisites inside skills.
- Opaque binaries, symlinked skill resources, or hidden install-time execution.
- Paid model evaluation in public CI or a formal scored evaluation suite for every skill.
- Per-skill semantic releases or npm publication of the repository tooling.
- Long-term support for previous Codex, Claude Code, skills CLI, or Node versions beyond the declared current support policy.
- Guaranteeing skills.sh indexing, ranking, telemetry behavior, or indexing latency.
- Transferring the repository to an organization or establishing open multi-maintainer governance in the initial version.

## Further Notes

- The repository currently contains only the engineering-skills configuration for local Markdown tracking, default triage labels, and single-context domain documentation. It has no commits, remote, application modules, skills, or test suite.
- The spec is intentionally ready for an implementation agent, but creating the future GitHub remote and enabling branch protection or private vulnerability reporting remain human administrative steps.
- The portable skill contract should follow the [Agent Skills specification](https://agentskills.io/specification).
- Codex-specific discovery and presentation behavior should be checked against the [official Codex skills documentation](https://developers.openai.com/codex/skills/).
- Claude-specific discovery and extension behavior should be checked against the [official Claude Code skills documentation](https://code.claude.com/docs/en/skills).
- CLI discovery, installation, telemetry, and lock behavior should be checked against the official [skills CLI repository](https://github.com/vercel-labs/skills) and [skills.sh documentation](https://www.skills.sh/docs).
- Tool versions and current-client behavior are time-sensitive. Implementation should pin the versions it validates and record them in compatibility documentation rather than relying on unqualified “latest” behavior.
