from pathlib import Path
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from app.adapters.memory_documents import InMemoryDocumentRepository
from app.adapters.memory_queue import InMemoryQueue
from app.adapters.memory_storage import InMemoryStorage
from app.api.deps import get_documents, get_queue, get_storage
from app.main import app

EVALS_DIR = Path(__file__).parents[2] / "evals"
SAMPLE_PDF = (EVALS_DIR / "samples" / "00_de_purchase_order.pdf").read_bytes()


@pytest.fixture
def queue():
    return InMemoryQueue()


@pytest.fixture
def client(queue):
    storage = InMemoryStorage()
    documents = InMemoryDocumentRepository()
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
