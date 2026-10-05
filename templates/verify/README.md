# `verify-<repo>` template

Every project gets one verification skill so every agent proves behavior the same way instead of improvising a script each session. It lives in the project, at `.agents/skills/verify-<repo>/`, because it knows how that app starts.

## Shape

```
.agents/skills/verify-<repo>/
  SKILL.md            ← from SKILL.md.tmpl (under 150 lines)
  bin/verify          ← the CLI; deterministic, no agent judgment
  features/
    README.md         ← the feature map index, in proof order
    <feature>.md      ← how a user reaches it + the observable result that proves it
```

## The CLI contract

| Command | Must do |
|---|---|
| `launch` | Start a disposable instance from the current checkout, isolated from personal config, and print how to reach it |
| `doctor` | Fail unless the running build is exactly `HEAD`, dependencies are healthy and no external service can be reached by accident |
| `api` / `sql` (or the app's equivalents) | Drive the app like a client and read its state; every step asserts its expected status or rows; `--save` keeps evidence |
| `diff` | Compare two captures, ignoring volatile fields, to prove "no behavior change" |
| `prove` | Clean start → every feature drive block in map order → teardown; exit 0 only when every step passes |
| `cleanup` | Stop only what `launch` started; keep the evidence |

## Rules that keep it honest

- A guard test in the project fails when a new entry point (route, command, screen) is missing from `features/`.
- `prove` never weakens an expectation to pass; a defect found by the verifier is listed in the map as evidence until it is fixed.
- The verifier must be able to fail: `audit-verification` breaks an expectation on purpose and expects red.
- Build it by interrogating the repo, not the user: how the app starts, authenticates, what can be driven and what evidence can be captured. Prove it once end to end before calling it done.
