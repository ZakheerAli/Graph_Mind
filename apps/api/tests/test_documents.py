from fastapi.testclient import TestClient

from apps.api.app.main import app
from apps.api.app.services.documents import get_document_service

client = TestClient(app)


def test_upload_document_creates_ready_record() -> None:
    content = "GraphMind is a document Q&A tool with citations.\n\nIt uses chunked retrieval."
    response = client.post(
        "/v1/documents",
        files={"file": ("notes.txt", content, "text/plain")},
        headers={"X-User-Id": "alice"},
    )

    assert response.status_code == 201
    payload = response.json()
    assert payload["status"] == "READY"
    assert payload["filename"] == "notes.txt"
    assert payload["document_id"]

    list_response = client.get("/v1/documents", headers={"X-User-Id": "alice"})
    assert list_response.status_code == 200
    documents = list_response.json()
    assert len(documents) == 1
    assert documents[0]["title"] == "notes"


def test_upload_rejects_missing_file_name() -> None:
    service = get_document_service()

    try:
        service.upload_document("", b"hello world", "alice")
    except ValueError as exc:
        assert "A file name is required" in str(exc)
    else:
        raise AssertionError("Expected ValueError for an empty filename")


def test_delete_document_removes_it() -> None:
    response = client.post(
        "/v1/documents",
        files={"file": ("delete-me.txt", "delete me", "text/plain")},
        headers={"X-User-Id": "alice"},
    )
    document_id = response.json()["document_id"]

    delete_response = client.delete(
        f"/v1/documents/{document_id}",
        headers={"X-User-Id": "alice"},
    )
    assert delete_response.status_code == 204

    remaining = client.get("/v1/documents", headers={"X-User-Id": "alice"})
    assert remaining.status_code == 200
    assert all(item["id"] != document_id for item in remaining.json())
