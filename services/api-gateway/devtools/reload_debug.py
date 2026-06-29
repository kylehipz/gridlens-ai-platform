from __future__ import annotations

import os
from pathlib import Path
import signal
import subprocess
import sys
import time


def source_snapshot(path: Path) -> dict[Path, int]:
    snapshot: dict[Path, int] = {}
    if not path.exists():
        return snapshot

    for source_file in path.rglob("*.py"):
        try:
            snapshot[source_file] = source_file.stat().st_mtime_ns
        except FileNotFoundError:
            continue
    return snapshot


def terminate(process: subprocess.Popen[object]) -> None:
    if process.poll() is not None:
        return

    process.terminate()
    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait()


def run_with_reload(module: str, port_env: str, source_dir: Path) -> int:
    debug_port = os.getenv(port_env)
    if debug_port is None:
        raise RuntimeError(f"{port_env} must be set")

    poll_seconds = float(os.getenv("DEV_RELOAD_POLL_SECONDS", "1"))
    child: subprocess.Popen[object] | None = None
    stopping = False

    def stop(_signum: int, _frame: object) -> None:
        nonlocal stopping
        stopping = True
        if child is not None:
            terminate(child)

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    snapshot = source_snapshot(source_dir)
    while not stopping:
        command = [
            sys.executable,
            "-m",
            "debugpy",
            "--listen",
            f"0.0.0.0:{debug_port}",
            "-m",
            module,
        ]
        child = subprocess.Popen(command)

        while not stopping and child.poll() is None:
            time.sleep(poll_seconds)
            next_snapshot = source_snapshot(source_dir)
            if next_snapshot != snapshot:
                snapshot = next_snapshot
                terminate(child)
                break

        if stopping:
            break
        if child.poll() is not None:
            return child.returncode

    return 0


def main() -> None:
    if len(sys.argv) != 4:
        print(
            "usage: reload_debug.py <module> <debug-port-env> <source-dir>",
            file=sys.stderr,
        )
        raise SystemExit(2)

    raise SystemExit(run_with_reload(sys.argv[1], sys.argv[2], Path(sys.argv[3])))


if __name__ == "__main__":
    main()
