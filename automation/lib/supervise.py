#!/usr/bin/env python3
"""Runs one automation job with the project lock held, in its own process group.

  supervise.py <lock-file> <wait-seconds> <poll-seconds> -- <command...>

The project is free only when nobody holds the flock AND the process group of the previous job is
gone: a worker can outlive a supervisor killed with SIGKILL, and it still owns the clone.
Busy past the wait: runs the command with KITCHEN_LOCK_STATE=busy, so the job records the skip itself.
Acquired: runs it with KITCHEN_LOCK_STATE=held in a new session. When its main process exits, or the
supervisor is told to stop (the signal is forwarded to the group first), every process left in the
group is terminated before the lock is released.
"""
import fcntl
import os
import signal
import subprocess
import sys
import time

GRACE = float(os.environ.get("KITCHEN_STOP_GRACE_SECONDS", "10"))
DRAIN = 2.0  # lets the job's log tee flush after its main process exits


def group_alive(pgid: int) -> bool:
    if pgid <= 1:
        return False
    try:
        os.killpg(pgid, 0)
        return True
    except ProcessLookupError:
        return False
    except PermissionError:  # the number now belongs to someone else's processes, not to our job
        return False


def recorded_group(fd: int) -> int:
    os.lseek(fd, 0, os.SEEK_SET)
    text = os.read(fd, 64).decode(errors="replace").strip()
    return int(text) if text.isdigit() else 0


def record_group(fd: int, pgid: int | None) -> None:
    os.ftruncate(fd, 0)
    os.lseek(fd, 0, os.SEEK_SET)
    if pgid:
        os.write(fd, f"{pgid}\n".encode())


def acquire(fd: int, wait: float, poll: float) -> bool:
    deadline = time.monotonic() + wait
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            if not group_alive(recorded_group(fd)):
                return True
            fcntl.flock(fd, fcntl.LOCK_UN)
        except BlockingIOError:
            pass
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            return False
        time.sleep(min(poll, remaining))


def stop_group(pgid: int, grace: float) -> None:
    end = time.monotonic() + DRAIN
    while group_alive(pgid) and time.monotonic() < end:
        time.sleep(0.05)
    for sig, wait in ((signal.SIGTERM, grace), (signal.SIGKILL, 5.0)):
        try:
            os.killpg(pgid, sig)
        except ProcessLookupError:
            return
        end = time.monotonic() + wait
        while group_alive(pgid) and time.monotonic() < end:
            time.sleep(0.05)
        if not group_alive(pgid):
            return


def main() -> int:
    lock_file, wait, poll, separator, *command = sys.argv[1:]
    if separator != "--" or not command:
        print("usage: supervise.py <lock-file> <wait> <poll> -- <command...>", file=sys.stderr)
        return 2
    fd = os.open(lock_file, os.O_RDWR | os.O_CREAT, 0o644)  # not inherited by the job
    if not acquire(fd, float(wait), float(poll)):
        os.close(fd)
        os.execvpe(command[0], command, {**os.environ, "KITCHEN_LOCK_STATE": "busy"})
    job = subprocess.Popen(command, env={**os.environ, "KITCHEN_LOCK_STATE": "held"}, start_new_session=True)
    record_group(fd, job.pid)

    def forward(sig, _frame):
        try:
            os.killpg(job.pid, sig)
        except ProcessLookupError:
            pass

    for sig in (signal.SIGTERM, signal.SIGINT, signal.SIGHUP):
        signal.signal(sig, forward)
    code = job.wait()
    stop_group(job.pid, GRACE)
    record_group(fd, None)
    os.close(fd)  # releases the lock
    return code if code >= 0 else 128 - code


if __name__ == "__main__":
    sys.exit(main())
