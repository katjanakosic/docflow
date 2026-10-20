"""Generate fake supplier invoices and purchase orders for DocFlow tests and evals."""

import json
import random
from dataclasses import dataclass, field
from datetime import date, timedelta
from decimal import ROUND_HALF_UP, Decimal
from pathlib import Path

from faker import Faker
from fpdf import FPDF


CENT = Decimal("0.01")


@dataclass
class LineItem:
    description: str
    quantity: int
    unit_price: Decimal

    @property
    def line_total(self) -> Decimal:
        return (self.unit_price * self.quantity).quantize(CENT, ROUND_HALF_UP)


@dataclass
class SampleDocument:
    doc_type: str  # invoice or purchase_order
    language: str  # de, fr, it or en
    supplier_name: str
    supplier_address: str
    supplier_vat_id: str
    document_number: str
    issue_date: date
    due_date: date | None
    currency: str
    vat_rate: Decimal
    line_items: list[LineItem] = field(default_factory=list)

    @property
    def subtotal(self) -> Decimal:
        return sum((item.line_total for item in self.line_items), Decimal("0"))

    @property
    def vat_amount(self) -> Decimal:
        return (self.subtotal * self.vat_rate / 100).quantize(CENT, ROUND_HALF_UP)

    @property
    def total(self) -> Decimal:
        return self.subtotal + self.vat_amount

# Faker locale per document language.
LOCALES = {"de": "de_CH", "fr": "fr_CH", "it": "it_IT", "en": "de_CH"}

COMPANY_SUFFIXES = {
    "de": ["AG", "GmbH"],
    "fr": ["SA", "Sàrl"],
    "it": ["SA", "Sagl"],
    "en": ["AG", "Ltd"],
}

VAT_SUFFIXES = {"de": "MWST", "fr": "TVA", "it": "IVA", "en": "MWST"}

NUMBER_PREFIXES = {
    "invoice": {"de": "RE", "fr": "FA", "it": "FT", "en": "INV"},
    "purchase_order": {"de": "BE", "fr": "BC", "it": "OA", "en": "PO"},
}

PRODUCTS = {
    "de": ["Bürostuhl", "Schreibtisch", "Druckerpapier A4", "Kugelschreiber (10er-Pack)",
           "Monitor 27 Zoll", "Aktenordner", "Tischlampe", "Whiteboard"],
    "fr": ["Chaise de bureau", "Bureau", "Papier d'imprimante A4", "Stylos (paquet de 10)",
           "Écran 27 pouces", "Classeur", "Lampe de bureau", "Tableau blanc"],
    "it": ["Sedia da ufficio", "Scrivania", "Carta per stampante A4", "Penne (confezione da 10)",
           "Monitor 27 pollici", "Raccoglitore", "Lampada da tavolo", "Lavagna bianca"],
    "en": ["Office chair", "Desk", "Printer paper A4", "Pens (pack of 10)",
           "27-inch monitor", "Ring binder", "Desk lamp", "Whiteboard"],
}
PRICE_RANGES = [(120, 350), (250, 900), (5, 15), (4, 12), (180, 450), (3, 9), (25, 80), (60, 200)]

VAT_RATES = [Decimal("8.1"), Decimal("2.6")]
CURRENCIES = ["CHF", "CHF", "CHF", "EUR"]

# Faker's Italian city names aren't reproducible across runs => use a fixed list
ITALIAN_CITIES = ["Milano", "Como", "Varese", "Torino", "Bergamo", "Brescia", "Verona", "Bologna"]


def random_document(index: int, seed: int = 42) -> SampleDocument:
    """
    Creates one fake document.
    The same index and seed always give the same document.
    """

    rng = random.Random(seed + index)
    language = list(LOCALES)[index % len(LOCALES)]
    fake = Faker(LOCALES[language])
    fake.seed_instance(seed + index)

    doc_type = "purchase_order" if index % 3 == 0 else "invoice"
    issue_date = date(2026, 1, 1) + timedelta(days=rng.randint(0, 270))
    due_date = issue_date + timedelta(days=30) if doc_type == "invoice" else None

    product_indexes = rng.sample(range(len(PRODUCTS[language])), rng.randint(1, 6))
    line_items = []
    for i in product_indexes:
        low, high = PRICE_RANGES[i]
        price = Decimal(rng.randint(low * 100, high * 100)) / 100
        line_items.append(LineItem(PRODUCTS[language][i], rng.randint(1, 20), price))

    city = rng.choice(ITALIAN_CITIES) if language == "it" else fake.city()

    return SampleDocument(
        doc_type=doc_type,
        language=language,
        supplier_name=f"{fake.last_name()} {rng.choice(COMPANY_SUFFIXES[language])}",
        supplier_address=f"{fake.street_address()}, {fake.postcode()} {city}",
        supplier_vat_id=(
            f"CHE-{rng.randint(100, 999)}.{rng.randint(100, 999)}.{rng.randint(100, 999)} "
            f"{VAT_SUFFIXES[language]}"
        ),
        document_number=f"{NUMBER_PREFIXES[doc_type][language]}-{rng.randint(10000, 99999)}",
        issue_date=issue_date,
        due_date=due_date,
        currency=rng.choice(CURRENCIES),
        vat_rate=rng.choice(VAT_RATES),
        line_items=line_items,
    )


CUSTOMER = "Alpenhandel AG, Bahnhofstrasse 10, 8001 Zürich"

LABELS = {
    "de": {"invoice": "Rechnung", "purchase_order": "Bestellung", "number": "Nummer",
           "date": "Datum", "due": "Zahlbar bis", "to": "An", "description": "Beschreibung",
           "qty": "Menge", "unit_price": "Einzelpreis", "amount": "Betrag",
           "subtotal": "Zwischensumme", "vat": "MWST", "total": "Total"},
    "fr": {"invoice": "Facture", "purchase_order": "Bon de commande", "number": "Numéro",
           "date": "Date", "due": "Payable jusqu'au", "to": "À", "description": "Description",
           "qty": "Quantité", "unit_price": "Prix unitaire", "amount": "Montant",
           "subtotal": "Sous-total", "vat": "TVA", "total": "Total"},
    "it": {"invoice": "Fattura", "purchase_order": "Ordine d'acquisto", "number": "Numero",
           "date": "Data", "due": "Scadenza", "to": "A", "description": "Descrizione",
           "qty": "Quantità", "unit_price": "Prezzo unitario", "amount": "Importo",
           "subtotal": "Subtotale", "vat": "IVA", "total": "Totale"},
    "en": {"invoice": "Invoice", "purchase_order": "Purchase order", "number": "Number",
           "date": "Date", "due": "Due date", "to": "To", "description": "Description",
           "qty": "Qty", "unit_price": "Unit price", "amount": "Amount",
           "subtotal": "Subtotal", "vat": "VAT", "total": "Total"},
}


def format_date(value: date, language: str) -> str:
    if language == "it":
        return value.strftime("%d/%m/%Y")
    if language == "en":
        return value.strftime("%Y-%m-%d")
    return value.strftime("%d.%m.%Y")  # de and fr


def format_money(amount: Decimal, language: str) -> str:
    text = f"{amount:,.2f}"  # e.g. 11,171.62
    separator = " " if language == "fr" else "'"
    return text.replace(",", separator)  # e.g. 11'171.62 or 11 171.62


def render_pdf(doc: SampleDocument, path: Path) -> None:
    """Draw one document as a single-page PDF."""
    labels = LABELS[doc.language]
    pdf = FPDF()
    pdf.add_page()

    def line(text: str, size: int = 10, bold: bool = False, height: int = 5) -> None:
        pdf.set_font("Helvetica", "B" if bold else "", size)
        pdf.cell(0, height, text, new_x="LMARGIN", new_y="NEXT")

    # Supplier and customer
    line(doc.supplier_name, size=14, bold=True, height=8)
    line(doc.supplier_address)
    line(doc.supplier_vat_id)
    pdf.ln(8)
    line(f"{labels['to']}: {CUSTOMER}")
    pdf.ln(8)

    # Title, number and dates
    line(labels[doc.doc_type], size=16, bold=True, height=10)
    line(f"{labels['number']}: {doc.document_number}")
    line(f"{labels['date']}: {format_date(doc.issue_date, doc.language)}")
    if doc.due_date:
        line(f"{labels['due']}: {format_date(doc.due_date, doc.language)}")
    pdf.ln(8)

    # Line items table: (text, width, alignment) per column
    def row(cells: list[tuple[str, int, str]], bold: bool = False) -> None:
        pdf.set_font("Helvetica", "B" if bold else "", 10)
        for text, width, align in cells:
            pdf.cell(width, 7, text, border=1, align=align)
        pdf.ln()

    widths = (95, 20, 35, 40)
    row([(labels["description"], widths[0], "L"), (labels["qty"], widths[1], "R"),
         (labels["unit_price"], widths[2], "R"), (labels["amount"], widths[3], "R")], bold=True)
    for item in doc.line_items:
        row([(item.description, widths[0], "L"), (str(item.quantity), widths[1], "R"),
             (format_money(item.unit_price, doc.language), widths[2], "R"),
             (format_money(item.line_total, doc.language), widths[3], "R")])

    # Totals, right-aligned under the table
    pdf.ln(4)
    totals = [
        (labels["subtotal"], doc.subtotal, False),
        (f"{labels['vat']} {doc.vat_rate}%", doc.vat_amount, False),
        (labels["total"], doc.total, True),
    ]
    for label, amount, bold in totals:
        pdf.set_font("Helvetica", "B" if bold else "", 10)
        pdf.cell(150, 6, label, align="R")
        pdf.cell(40, 6, f"{doc.currency} {format_money(amount, doc.language)}", align="R",
                 new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(path))


SAMPLE_COUNT = 20
EVALS_DIR = Path(__file__).parent
SAMPLES_DIR = EVALS_DIR / "samples"
LABELS_PATH = EVALS_DIR / "labels.json"


def money(value: Decimal) -> str:
    """Money as exact text with two decimals, e.g. '12.00'."""
    return str(value.quantize(CENT))


def to_label(doc: SampleDocument) -> dict:
    """The values an extractor should find in this document."""
    return {
        "doc_type": doc.doc_type,
        "language": doc.language,
        "supplier_name": doc.supplier_name,
        "supplier_vat_id": doc.supplier_vat_id,
        "document_number": doc.document_number,
        "issue_date": doc.issue_date.isoformat(),
        "due_date": doc.due_date.isoformat() if doc.due_date else None,
        "currency": doc.currency,
        "line_items": [
            {
                "description": item.description,
                "quantity": item.quantity,
                "unit_price": money(item.unit_price),
                "line_total": money(item.line_total),
            }
            for item in doc.line_items
        ],
        "subtotal": money(doc.subtotal),
        "vat_rate": str(doc.vat_rate),
        "vat_amount": money(doc.vat_amount),
        "total": money(doc.total),
    }


def main() -> None:
    SAMPLES_DIR.mkdir(exist_ok=True)
    labels = {}
    for index in range(SAMPLE_COUNT):
        doc = random_document(index)
        file_name = f"{index:02d}_{doc.language}_{doc.doc_type}.pdf"
        render_pdf(doc, SAMPLES_DIR / file_name)
        labels[file_name] = to_label(doc)

    LABELS_PATH.write_text(json.dumps(labels, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {SAMPLE_COUNT} documents to {SAMPLES_DIR} and labels to {LABELS_PATH}")


if __name__ == "__main__":
    main()