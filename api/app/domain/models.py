from datetime import date
from decimal import Decimal
from enum import StrEnum

from pydantic import BaseModel, Field


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
