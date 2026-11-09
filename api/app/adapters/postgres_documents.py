"""Document records in Postgres."""

from uuid import UUID

from sqlalchemy import (
    Column,
    DateTime,
    Engine,
    Integer,
    MetaData,
    String,
    Table,
    Text,
    Uuid,
    insert,
    select,
    update,
)
from sqlalchemy.dialects.postgresql import JSONB

from app.domain.models import Document, ExtractedData
from app.domain.ports import DocumentNotFoundError
from app.domain.state_machine import Status

metadata = MetaData()

# Describes the table the migration created, so SQLAlchemy can build queries for it
documents_table = Table(
    "documents",
    metadata,
    Column("id", Uuid, primary_key=True),
    Column("file_name", Text, nullable=False),
    Column("sha256", String(64), nullable=False),
    Column("size_bytes", Integer, nullable=False),
    Column("storage_key", Text, nullable=False),
    Column("uploaded_by", Text, nullable=False),
    Column("status", String(32), nullable=False),
    Column("created_at", DateTime(timezone=True), nullable=False),
    Column("extracted_data", JSONB, nullable=True),
    Column("last_error", Text, nullable=True),
    Column("reviewed_by", Text, nullable=True),
    Column("reviewed_at", DateTime(timezone=True), nullable=True),
    Column("rejection_reason", Text, nullable=True),
)


def _to_row(document: Document) -> dict:
    """A Document as column values."""
    return {
        "id": document.id,
        "file_name": document.file_name,
        "sha256": document.sha256,
        "size_bytes": document.size_bytes,
        "storage_key": document.storage_key,
        "uploaded_by": document.uploaded_by,
        "status": document.status.value,
        "created_at": document.created_at,
        "extracted_data": (
            document.extracted_data.model_dump(mode="json")
            if document.extracted_data
            else None
        ),
        "last_error": document.last_error,
        "reviewed_by": document.reviewed_by,
        "reviewed_at": document.reviewed_at,
        "rejection_reason": document.rejection_reason,
    }


def _to_document(row) -> Document:
    """A row from the table as a Document."""
    data = row["extracted_data"]
    return Document(
        id=row["id"],
        file_name=row["file_name"],
        sha256=row["sha256"],
        size_bytes=row["size_bytes"],
        storage_key=row["storage_key"],
        uploaded_by=row["uploaded_by"],
        status=Status(row["status"]),
        created_at=row["created_at"],
        extracted_data=ExtractedData.model_validate(data) if data is not None else None,
        last_error=row["last_error"],
        reviewed_by=row["reviewed_by"],
        reviewed_at=row["reviewed_at"],
        rejection_reason=row["rejection_reason"],
    )


class PostgresDocumentRepository:
    def __init__(self, engine: Engine) -> None:
        self._engine = engine

    def add(self, document: Document) -> None:
        with self._engine.begin() as connection:
            connection.execute(insert(documents_table).values(**_to_row(document)))

    def get(self, document_id: UUID) -> Document:
        query = select(documents_table).where(documents_table.c.id == document_id)
        with self._engine.connect() as connection:
            row = connection.execute(query).mappings().first()
        if row is None:
            raise DocumentNotFoundError(document_id)
        return _to_document(row)

    def update(self, document: Document) -> None:
        statement = (
            update(documents_table)
            .where(documents_table.c.id == document.id)
            .values(**_to_row(document))
        )
        with self._engine.begin() as connection:
            result = connection.execute(statement)
        if result.rowcount == 0:
            raise DocumentNotFoundError(document.id)

    def find_by_sha256(self, sha256: str) -> list[Document]:
        query = (
            select(documents_table)
            .where(documents_table.c.sha256 == sha256)
            .order_by(documents_table.c.created_at)
        )
        with self._engine.connect() as connection:
            rows = connection.execute(query).mappings().all()
        return [_to_document(row) for row in rows]

    def list_recent(self, limit: int) -> list[Document]:
        query = (
            select(documents_table)
            .order_by(documents_table.c.created_at.desc())
            .limit(limit)
        )
        with self._engine.connect() as connection:
            rows = connection.execute(query).mappings().all()
        return [_to_document(row) for row in rows]
