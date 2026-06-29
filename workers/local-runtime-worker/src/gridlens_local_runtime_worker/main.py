import os
import signal
import sys
import time


def heartbeat_message() -> str:
    return "gridlens local runtime worker ready"


def main() -> None:
    interval = float(os.getenv("WORKER_HEARTBEAT_SECONDS", "30"))
    running = True

    def stop(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    print(heartbeat_message(), flush=True)
    while running:
        time.sleep(interval)
        if running:
            print(heartbeat_message(), flush=True)

    print("gridlens local runtime worker stopping", flush=True)
    sys.exit(0)


if __name__ == "__main__":
    main()
