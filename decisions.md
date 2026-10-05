# Decisions

One entry per decision: date, decision, scope, when to revisit. `- [ ]` marks a decision the owner still owes (`kitchen status` counts them); close it as `- [x]` with the date and the answer.

## Owed

- [ ] Require a status check on `main` with a ruleset (one-way door; `kitchen init --check .` prints the command).

## Decided

- 2026-10-05. **Principles, not more skills.** The kitchen's direction lives in one file, `PRINCIPLES.md`: what we do and why, so an agent can decide the way the owner would. Scope: the whole kitchen. Revisit when a principle has no control and no "rule only" note.
- 2026-10-05. **All 24 pstack principles are folded in** under the kitchen's 13, by their own names, plus a 13th principle, `design`, for the code-design ones. Scope: `PRINCIPLES.md`. Revisit when pstack changes its list.
- 2026-10-05. **Two conflicts settled in favor of the owner's rules:** a legacy path is deleted in the same change only when no behavior anyone relies on is lost (published contracts stay one-way doors); "never block on the human" never covers one-way doors or anything published or sent to people. Scope: `no-fallbacks`, `owner-attention`, `doors`.
- 2026-10-05. **The index goes in the AGENTS.md every agent reads.** `kitchen install` writes `~/.claude/CLAUDE.md` and `~/.codex/AGENTS.md` from the person's own rules plus one line per principle; the detail stays in `PRINCIPLES.md`, read on demand. Codex reads one global file and has no include, so the file is generated, not linked. Scope: install, doctor. Revisit if Codex gains includes.
- 2026-10-05. **Each person has their own rules.** `kitchen install --rules <file>|global|none`, remembered in `~/.config/kitchen/rules.txt`; the kitchen's `global/AGENTS.md` are its owner's rules, the default when nobody chose. Scope: install, for teammates. Revisit when a teammate installs.
- 2026-10-05. **pstack's mechanical checks hang on steps that already run** (the reviewer lenses of `second-opinion`, `find-the-cause`, `retro`); no new skill or step. Scope: skills.
- 2026-10-05. **`kitchen adopt` became `kitchen init`, per repo, never automatic.** It checks, asks numbered questions with recommendations (a terminal), or takes `--yes`/`--prove`/`--base` (an agent), then writes the shared layer on branch `kitchen/init` and the personal layer in `~/.config/kitchen`. `install` offers it for all listed repos, one, or none. Scope: `kitchen init`, `kitchen install`.
- 2026-10-05. **Agent hooks travel with the repo** (option A): `kitchen init` proposes a copy under `.kitchen/hooks/` and a `.claude/settings.json` that runs it, failing closed when the copy is missing, so teammates and cloud sessions get the guards without installing the kitchen; `init --check` fails on a stale copy. Measured: Claude Code loads it in a session started at the repo root; Codex 0.160 loaded no project hooks in three probes, so no `.codex/hooks.json` is proposed. Scope: `kitchen init`. Revisit when Codex loads project hooks, and after measuring the cloud environments.
- 2026-10-05. **The principles travel with the repo too:** `kitchen init` proposes `.kitchen/PRINCIPLES.md` (an eleventh must-have, `principles`) and the AGENTS.md line that names it, so a teammate or a cloud session with only the repo reads them. Scope: `kitchen init`.
- 2026-10-05. **init refreshes its own copies:** a copy of the kitchen's files that init wrote and nobody edited (sha256 matches `.kitchen/init.json`) follows the kitchen; an edited copy is left alone and reported. Scope: `kitchen init`.
- 2026-10-05. **Stale generated rules are an exception in `kitchen status`,** not only in `doctor`. Scope: status, doctor.
- 2026-10-05. **One model role, `reviewer`, until a workflow reads another** (option B; verifier, worker and explorer were dropped the same day, unused). Scope: `kitchen models`.
- 2026-10-05. **Models per role are each person's setup**, never fixed in a repo. A model that is not available fails when used, with the role and model named; no other model stands in. Scope: `kitchen models`, `second-opinion`.
- 2026-10-05. **A thin T3 layer, in the rules that already exist:** workers that edit get their own worktree through `t3_thread_launch`, reviews and probes go through `delegate_task`, PRs are watched with `watch_pull_request`, UI is checked with `preview_*`/`device_*`; each with its plain equivalent outside T3. `$V prove` stays the verification gate. Scheduled jobs stay on launchd/systemd, which run with T3 closed. Measured in T3 the same day: `deny-recursive-rm` blocks under the Codex provider; a manual skill sent as `$make-me-realize` ran under Codex; sent as `/make-me-realize` through `delegate_task`, Claude's harness did not expand it and the agent loaded it with its Skill tool. Not measured: a slash command typed in T3's composer. Scope: `global/AGENTS.md`, `templates/verify`.
- 2026-10-05. **A retro proposes a fix only for what an earlier retro already listed** (or what did real damage); first-time groups go to a Watch list. Scope: the `retro` skill.
- 2026-10-05. **Verification-method questions (evening retro, row 2): deferred.** The rule that makes Codex ask (`global/AGENTS.md`, "agree it with me") stays for now. Revisit at the next retro.
- 2026-10-05. **Worktrees: the global rule stays; MaxOne is the exception** (option A): its AGENTS.md says workers share the main checkout. Scope: MaxOne.
- 2026-10-05. **Not exclusive to T3 Code.** Everything must work in the Claude Code and Codex CLIs, in T3 Code and in cloud sessions; T3's tools are one transport among several. Scope: the whole kitchen.
- 2026-10-05. **p3-stack is not installed.** Its ideas were read; re-evaluate in a few weeks. Scope: the kitchen.
