import json
import os
import signal
from threading import Event

SERVICE_NAME = "program-evaluation-service"
WORKER_NAME = "program-evaluation-worker"


def readiness() -> dict[str, str]:
    return {"status": "ready", "service": SERVICE_NAME, "worker": WORKER_NAME}


def main() -> None:
    interval = float(os.getenv("WORKER_HEARTBEAT_SECONDS", "30"))
    stop_event = Event()

    def stop(_signum: int, _frame: object) -> None:
        stop_event.set()

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)

    while not stop_event.is_set():
        print(json.dumps(readiness(), sort_keys=True), flush=True)
        stop_event.wait(interval)


if __name__ == "__main__":
    main()
