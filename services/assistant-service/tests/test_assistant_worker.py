from gridlens_assistant_service.workers import readiness


def test_worker_readiness_is_deterministic() -> None:
    assert readiness() == {
        "status": "ready",
        "service": "assistant-service",
        "worker": "assistant-worker",
    }
