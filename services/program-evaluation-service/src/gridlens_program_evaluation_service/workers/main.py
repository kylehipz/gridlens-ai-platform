import json

SERVICE_NAME = "program-evaluation-service"
WORKER_NAME = "program-evaluation-worker"


def readiness() -> dict[str, str]:
    return {"status": "ready", "service": SERVICE_NAME, "worker": WORKER_NAME}


def main() -> None:
    print(json.dumps(readiness(), sort_keys=True))
