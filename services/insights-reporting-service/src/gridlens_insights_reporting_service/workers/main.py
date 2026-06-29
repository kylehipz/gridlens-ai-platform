import json

SERVICE_NAME = "insights-reporting-service"
WORKER_NAME = "insights-reporting-worker"


def readiness() -> dict[str, str]:
    return {"status": "ready", "service": SERVICE_NAME, "worker": WORKER_NAME}


def main() -> None:
    print(json.dumps(readiness(), sort_keys=True))
