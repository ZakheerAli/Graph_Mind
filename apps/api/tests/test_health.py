from fastapi.testclient import TestClient

from apps.api.app.main import app

client = TestClient(app)


def test_health_reports_live_and_assigns_trace_id() -> None:
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
    assert response.headers["X-Trace-ID"]


def test_readiness_endpoint_reports_ready() -> None:
    response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
