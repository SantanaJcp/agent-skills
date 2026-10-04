#!/usr/bin/env python3
"""Runs a command with a deadline so a hung network call cannot hold a job (macOS has no timeout binary).

  bounded.py <seconds> <command...>

The command runs in its own process group so the whole tree can be stopped: on expiry SIGTERM, then
SIGKILL after 5 seconds, and exit 124 like coreutils timeout. A stop signal sent to this helper is
forwarded to that group.
"""
import os
import signal
import subprocess
import sys


def stop(proc: subprocess.Popen) -> None:
    for sig, wait in ((signal.SIGTERM, 5), (signal.SIGKILL, 5)):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            return
        try:
            proc.wait(timeout=wait)
            return
        except subprocess.TimeoutExpired:
            continue


def main() -> int:
    seconds, command = float(sys.argv[1]), sys.argv[2:]
    proc = subprocess.Popen(command, process_group=0)

    def forward(sig, _frame):
        try:
            os.killpg(proc.pid, sig)
        except ProcessLookupError:
            pass

    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, forward)
    try:
        code = proc.wait(timeout=seconds)
    except subprocess.TimeoutExpired:
        print(f"kitchen automation: {' '.join(command[:3])} timed out after {seconds:g}s", file=sys.stderr)
        stop(proc)
        return 124
    try:
        os.killpg(proc.pid, signal.SIGTERM)  # nothing the command started outlives it
    except ProcessLookupError:
        pass
    return code if code >= 0 else 128 - code


if __name__ == "__main__":
    sys.exit(main())
