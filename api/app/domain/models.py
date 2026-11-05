from dataclasses import dataclass, field
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, Field

from app.domain.state_machine import Action, Status, transition


class DocType(StrEnum):
    INVOICE = "invoice"
    PURCHASE_ORDER = "purchase_order"


class Currency(StrEnum):
    CHF = "CHF"
    EUR = "EUR"
    USD = "USD"


class ExtractedLineItem(BaseModel):
    description: str
    quantity: Decimal
    unit_price: Decimal
    line_total: Decimal


class ExtractedData(BaseModel):
    doc_type: DocType
    supplier_name: str
    supplier_vat_id: str | None = None
    document_number: str
    issue_date: date
    due_date: date | None = None
    po_reference: str | None = None
    currency: Currency
    line_items: list[ExtractedLineItem] = Field(min_length=1)
    subtotal: Decimal
    vat_amount: Decimal
    total: Decimal
    # How sure the extractor is about each field, from 0 to 1, e.g. {"total": 0.97}.
    confidence: dict[str, float] = Field(default_factory=dict)


@dataclass
class Document:
    """Record of one uploaded file and where it is in the workflow."""

    id: UUID
    file_name: str
    sha256: str  # fingerprint of the file's bytes, used to detect duplicate uploads
    size_bytes: int
    storage_key: str  # where the file lives in object storage
    uploaded_by: str  # the uploader's user id
    status: Status = Status.UPLOADED
    created_at: datetime = field(default_factory=lambda: datetime.now(UTC))
    extracted_data: ExtractedData | None = None  # filled in by a successful extraction
    last_error: str | None = None  # readable reason if extraction failed

    def apply(self, action: Action) -> None:
        """Change the status through the state machine; raises if not allowed."""
        self.status = transition(self.status, action)
