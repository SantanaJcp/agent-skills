#!/usr/bin/env python3
"""Claude Code settings that put an OS boundary around the gardener's tools.

  sandbox_settings.py --read PATH... [--write PATH...] [--domain NAME...] [--socket PATH...]

Reads are an allowlist (Claude Code settings reference: permissions.blockReadsOutsideWorkingDirectories,
sandbox.filesystem.denyRead / allowRead, "the rule with the narrower path applies"):
- blockReadsOutsideWorkingDirectories makes Read, Grep and Glob refuse paths outside the working
  directories, and denies sandboxed Bash the home directory and the other user roots (/Users, /home...);
- denyRead "~/" denies the whole home directory to Bash even where the block re-opens files, and
  allowRead re-opens exactly the --read paths (the clone, the run's work dir, the metrics history, and
  the tool or cache paths the project's build needs, from its config);
- the credential locations below stay denied even inside an allowed path (narrower deny wins).
Writes go only to the working directory, the session temp dir and the --write paths; network only to
the --domain names. failIfUnavailable and allowUnsandboxedCommands=false leave no way out. The claude
process itself stays outside the sandbox, so its own login and the model API keep working.
"""
import argparse
import json
import sys

CREDENTIAL_DIRS = ["~/.ssh", "~/Library/Keychains", "~/.config/gh", "~/.aws", "~/.config/gcloud", "~/.azure",
                   "~/.kube", "~/.docker", "~/.gnupg", "~/.codex", "~/.claude/projects"]
CREDENTIAL_FILES = ["~/.git-credentials", "~/.netrc", "~/.npmrc", "~/.pypirc", "~/.gitconfig"]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--read", action="append", default=[], required=True)
    parser.add_argument("--write", action="append", default=[])
    parser.add_argument("--domain", action="append", default=[])
    parser.add_argument("--socket", action="append", default=[])
    args = parser.parse_args()
    reads = [path for path in args.read if path]
    writes = [path for path in args.write if path]
    deny_rules = []
    for path in CREDENTIAL_DIRS:
        deny_rules += [f"Read({path}/**)", f"Edit({path}/**)"]
    for path in CREDENTIAL_FILES:
        deny_rules += [f"Read({path})", f"Edit({path})"]
    settings = {
        "sandbox": {
            "enabled": True,
            "failIfUnavailable": True,
            "allowUnsandboxedCommands": False,
            "filesystem": {
                "denyRead": ["~/"] + CREDENTIAL_DIRS + CREDENTIAL_FILES,
                "allowRead": reads,
                "allowWrite": writes,
            },
            "network": {"allowedDomains": [d for d in args.domain if d], "allowUnixSockets": [s for s in args.socket if s]},
        },
        "permissions": {"blockReadsOutsideWorkingDirectories": True, "deny": deny_rules},
    }
    print(json.dumps(settings, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
