from gridlens_data_operations_service.workers.main import readiness


def test_worker_readiness_is_deterministic() -> None:
    assert readiness() == {
        "status": "ready",
        "service": "data-operations-service",
        "worker": "data-operations-worker",
    }
