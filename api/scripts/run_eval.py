"""Measure the LLM extractor's accuracy against the labeled samples in evals/.

Run from api/:  uv run --env-file ../.env python -m scripts.run_eval
"""

import json
import time
from pathlib import Path

import anthropic

from app.adapters.llm_extractor import PROMPT_VERSION, LLMExtractor
from app.domain.models import ExtractedData
from app.domain.ports import ExtractionError

MODEL = "claude-haiku-5-5"
EVALS_DIR = Path(__file__).parents[2] / "evals"
RESULTS_DIR = EVALS_DIR / "results"
FIELDS = [
    "doc_type",
    "supplier_name",
    "supplier_vat_id",
    "document_number",
    "issue_date",
    "due_date",
    "currency",
    "subtotal",
    "vat_amount",
    "total",
]
ALL_FIELDS = [*FIELDS, "line_items"]


def line_items_match(expected: ExtractedData, actual: ExtractedData) -> bool:
    """
    Checks if two line-items are equal.
    """
    if len(expected.line_items) != len(actual.line_items):
        return False
    pairs = zip(expected.line_items, actual.line_items, strict=True)
    return all(e.model_dump() == a.model_dump() for e, a in pairs)


def compare(expected: ExtractedData, actual: ExtractedData) -> dict[str, bool]:
    """
    Checks one document against another. For each of the ten single fields, it checks whether the label’s value equals the model’s value.
    """
    results = {
        field: getattr(expected, field) == getattr(actual, field) for field in FIELDS
    }
    results["line_items"] = line_items_match(expected, actual)
    return results


def main() -> None:
    labels = json.loads((EVALS_DIR / "labels.json").read_text(encoding="utf-8"))
    extractor = LLMExtractor(anthropic.Anthropic(), model=MODEL)
    correct = dict.fromkeys(ALL_FIELDS, 0)
    report = []
    started = time.perf_counter()

    for file_name, label in labels.items():
        expected = ExtractedData.model_validate(label)
        pdf_bytes = (EVALS_DIR / "samples" / file_name).read_bytes()
        try:
            actual = extractor.extract(pdf_bytes)
        except ExtractionError as error:
            print(f"{file_name}: FAILED ({error})")
            report.append({"file": file_name, "error": str(error)})
            continue

        results = compare(expected, actual)
        for field, ok in results.items():
            correct[field] += ok
        wrong = [field for field, ok in results.items() if not ok]
        print(
            f"{file_name}: {'all correct' if not wrong else 'wrong: ' + ', '.join(wrong)}"
        )
        for field in wrong:
            if field != "line_items":
                print(
                    f"    {field}: expected {getattr(expected, field)!r}, got {getattr(actual, field)!r}"
                )
        report.append(
            {
                "file": file_name,
                "wrong": wrong,
                "extracted": actual.model_dump(mode="json"),
            }
        )

    count = len(labels)
    overall = sum(correct.values()) / (count * len(ALL_FIELDS))
    print(
        f"\nModel {MODEL}, prompt {PROMPT_VERSION}, {count} documents, "
        f"{time.perf_counter() - started:.0f} s"
    )
    for field in ALL_FIELDS:
        print(f"  {field:<16} {correct[field]}/{count}")
    print(f"  {'overall':<16} {overall:.1%}")

    RESULTS_DIR.mkdir(exist_ok=True)
    result_path = RESULTS_DIR / f"{PROMPT_VERSION}_{MODEL}.json"
    summary = {
        "model": MODEL,
        "prompt_version": PROMPT_VERSION,
        "overall": overall,
        "documents": report,
    }
    result_path.write_text(
        json.dumps(summary, indent=2, ensure_ascii=False) + "\n", encoding="utf-8"
    )
    print(f"Details saved to {result_path}")


if __name__ == "__main__":
    main()
