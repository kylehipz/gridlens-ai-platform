import json
import os
import signal
import time

SERVICE_NAME = "insights-reporting-service"
WORKER_NAME = "insights-reporting-worker"


def readiness() -> dict[str, str]:
    return {"status": "ready", "service": SERVICE_NAME, "worker": WORKER_NAME}


def main() -> None:
    interval = float(os.getenv("WORKER_HEARTBEAT_SECONDS", "30"))
    running = True

    def stop(_signum: int, _frame: object) -> None:
        nonlocal running
        running = False

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    while running:
        print(json.dumps(readiness(), sort_keys=True), flush=True)
        time.sleep(interval)
