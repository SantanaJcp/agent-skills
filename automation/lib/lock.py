#!/usr/bin/env python3
"""Holds a per-project lock for as long as the job that started it lives.

macOS has no flock binary, so the job starts this helper in the background:
  lock.py <lock-file> <wait-seconds> <poll-seconds> <answer-file>
It writes "acquired" or "busy" to <answer-file>. Once acquired it keeps the flock
until its parent job exits or kills it; the kernel releases the lock if it dies.
"""
import fcntl
import os
import sys
import time


def answer(path: str, word: str) -> None:
    tmp = f"{path}.tmp"
    with open(tmp, "w") as handle:
        handle.write(word + "\n")
    os.replace(tmp, path)


def main() -> int:
    lock_file, wait, poll, answer_file = sys.argv[1], float(sys.argv[2]), float(sys.argv[3]), sys.argv[4]
    owner = os.getppid()
    fd = os.open(lock_file, os.O_RDWR | os.O_CREAT, 0o644)
    deadline = time.monotonic() + wait
    while True:
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            break
        except BlockingIOError:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                answer(answer_file, "busy")
                return 75
            time.sleep(min(poll, remaining))
    os.ftruncate(fd, 0)
    os.write(fd, f"{owner}\n".encode())
    answer(answer_file, "acquired")
    while os.getppid() == owner:  # reparented means the job is gone
        time.sleep(1)
    return 0


if __name__ == "__main__":
    sys.exit(main())
