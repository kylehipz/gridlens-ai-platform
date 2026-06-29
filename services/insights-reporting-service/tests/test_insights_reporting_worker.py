from gridlens_insights_reporting_service.workers import readiness


def test_worker_readiness_is_deterministic() -> None:
    assert readiness() == {
        "status": "ready",
        "service": "insights-reporting-service",
        "worker": "insights-reporting-worker",
    }
