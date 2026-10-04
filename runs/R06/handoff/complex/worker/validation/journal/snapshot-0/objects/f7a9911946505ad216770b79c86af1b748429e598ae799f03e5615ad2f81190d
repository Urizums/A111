#!/usr/bin/env python3
"""Wait at a shared local gate, record release, then exec the real app process."""
import json
import os
import sys
import time
from datetime import datetime, timezone
from pathlib import Path


def main():
    if len(sys.argv) < 4:
        raise SystemExit("usage: concurrency_gate.py GATE MARKER COMMAND [ARG ...]")
    gate = Path(sys.argv[1])
    marker = Path(sys.argv[2])
    command = sys.argv[3:]
    while not gate.exists():
        time.sleep(0.002)
    record = {
        "pid": os.getpid(),
        "gate_observed_at": datetime.now(timezone.utc).isoformat(),
        "gate_observed_monotonic": time.monotonic(),
    }
    with marker.open("x", encoding="utf-8") as stream:
        json.dump(record, stream, ensure_ascii=False, sort_keys=True)
        stream.write("\n")
        stream.flush()
        os.fsync(stream.fileno())
    os.execv(command[0], command)


if __name__ == "__main__":
    main()
