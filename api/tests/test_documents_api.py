from pathlib import Path
from uuid import UUID, uuid4

import pytest
from fastapi.testclient import TestClient

from app.adapters.memory_documents import InMemoryDocumentRepository
from app.adapters.memory_queue import InMemoryQueue
from app.adapters.memory_storage import InMemoryStorage
from app.api.deps import get_documents, get_queue, get_storage
from app.domain.state_machine import Action
from app.main import app

EVALS_DIR = Path(__file__).parents[2] / "evals"
SAMPLE_PDF = (EVALS_DIR / "samples" / "00_de_purchase_order.pdf").read_bytes()


@pytest.fixture
def queue():
    return InMemoryQueue()


@pytest.fixture
def documents():
    return InMemoryDocumentRepository()


@pytest.fixture
def client(queue, documents):
    storage = InMemoryStorage()
    app.dependency_overrides[get_storage] = lambda: storage
    app.dependency_overrides[get_documents] = lambda: documents
    app.dependency_overrides[get_queue] = lambda: queue
    yield TestClient(app)
    app.dependency_overrides.clear()


def upload(client, content=SAMPLE_PDF, name="order.pdf"):
    return client.post(
        "/api/v1/documents", files={"file": (name, content, "application/pdf")}
    )


def test_upload_creates_a_document(client):
    response = upload(client)
    assert response.status_code == 201
    body = response.json()
    assert body["duplicate"] is False
    assert body["document"]["status"] == "uploaded"
    assert "storage_key" not in body["document"]  # internal fields stay hidden


def test_uploading_the_same_file_twice_returns_200_and_the_same_id(client):
    first = upload(client).json()
    response = upload(client)
    assert response.status_code == 200
    assert response.json()["duplicate"] is True
    assert response.json()["document"]["id"] == first["document"]["id"]


def test_uploading_a_non_pdf_returns_400(client):
    response = upload(client, content=b"just some text", name="notes.txt")
    assert response.status_code == 400
    assert response.json()["detail"] == "Only PDF files can be uploaded"


def test_an_uploaded_document_can_be_fetched(client):
    document_id = upload(client).json()["document"]["id"]
    response = client.get(f"/api/v1/documents/{document_id}")
    assert response.status_code == 200
    assert response.json()["file_name"] == "order.pdf"


def test_fetching_an_unknown_id_returns_404(client):
    response = client.get(f"/api/v1/documents/{uuid4()}")
    assert response.status_code == 404


def test_fetching_with_an_invalid_id_returns_422(client):
    response = client.get("/api/v1/documents/not-a-uuid")
    assert response.status_code == 422


def test_an_upload_queues_an_extraction_job(client, queue):
    document_id = upload(client).json()["document"]["id"]
    assert [str(queued) for queued in queue.enqueued] == [document_id]


def test_listing_documents_returns_the_newest_first(client):
    first = upload(client).json()["document"]["id"]
    second = upload(client, content=b"%PDF-1.4 second", name="second.pdf").json()[
        "document"
    ]["id"]

    response = client.get("/api/v1/documents")

    assert response.status_code == 200
    assert [d["id"] for d in response.json()] == [second, first]


def test_listing_respects_the_limit_and_rejects_invalid_values(client):
    upload(client)
    upload(client, content=b"%PDF-1.4 second", name="second.pdf")

    assert len(client.get("/api/v1/documents?limit=1").json()) == 1
    assert client.get("/api/v1/documents?limit=0").status_code == 422


def ready_for_review(client, documents) -> str:
    """Uploads the sample and moves it to needs_review, as the worker would."""
    document_id = upload(client).json()["document"]["id"]
    document = documents.get(UUID(document_id))
    document.apply(Action.START_EXTRACTION)
    document.apply(Action.EXTRACTION_SUCCEEDED)
    documents.update(document)
    return document_id


def test_approving_a_document(client, documents):
    document_id = ready_for_review(client, documents)
    response = client.post(f"/api/v1/documents/{document_id}/approve")

    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert response.json()["reviewed_by"] == "demo-user"


def test_approving_twice_returns_409(client, documents):
    document_id = ready_for_review(client, documents)
    client.post(f"/api/v1/documents/{document_id}/approve")
    assert client.post(f"/api/v1/documents/{document_id}/approve").status_code == 409


def test_rejecting_with_a_reason(client, documents):
    document_id = ready_for_review(client, documents)
    response = client.post(
        f"/api/v1/documents/{document_id}/reject",
        json={"reason": "Unreadable or incomplete"},
    )

    assert response.status_code == 200
    assert response.json()["status"] == "rejected"
    assert response.json()["rejection_reason"] == "Unreadable or incomplete"


def test_rejecting_without_a_reason_returns_422(client, documents):
    document_id = ready_for_review(client, documents)
    response = client.post(
        f"/api/v1/documents/{document_id}/reject", json={"reason": ""}
    )
    assert response.status_code == 422


def test_approving_an_unknown_document_returns_404(client):
    assert client.post(f"/api/v1/documents/{uuid4()}/approve").status_code == 404


def failed_extraction(client, documents) -> str:
    """Uploads the sample and marks its extraction as failed, as the worker would."""
    document_id = upload(client).json()["document"]["id"]
    document = documents.get(UUID(document_id))
    document.apply(Action.START_EXTRACTION)
    document.apply(Action.EXTRACTION_FAILED)
    document.last_error = "The AI service could not be reached."
    documents.update(document)
    return document_id


def test_retrying_a_failed_extraction_queues_it_again(client, documents, queue):
    document_id = failed_extraction(client, documents)
    response = client.post(f"/api/v1/documents/{document_id}/retry")

    assert response.status_code == 202
    assert response.json()["status"] == "uploaded"
    assert [str(queued) for queued in queue.enqueued] == [document_id, document_id]


def test_retrying_a_document_that_did_not_fail_returns_409(client, documents):
    document_id = ready_for_review(client, documents)
    assert client.post(f"/api/v1/documents/{document_id}/retry").status_code == 409


def test_the_file_endpoint_redirects_to_a_storage_link(client):
    document_id = upload(client).json()["document"]["id"]
    response = client.get(
        f"/api/v1/documents/{document_id}/file", follow_redirects=False
    )

    assert response.status_code == 307
    assert response.headers["location"].startswith("memory://documents/")


def test_the_file_of_an_unknown_document_returns_404(client):
    response = client.get(f"/api/v1/documents/{uuid4()}/file", follow_redirects=False)
    assert response.status_code == 404
