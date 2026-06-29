from gridlens_program_evaluation_service.workers import readiness


def test_worker_readiness_is_deterministic() -> None:
    assert readiness() == {
        "status": "ready",
        "service": "program-evaluation-service",
        "worker": "program-evaluation-worker",
    }
