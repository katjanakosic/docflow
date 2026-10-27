"""Extractor that returns known answers for the evals sample PDFs. AI pipeline added later."""

import hashlib
import json
from pathlib import Path

from app.domain.models import ExtractedData
from app.domain.ports import ExtractionError


class FakeExtractor:
    def __init__(self, samples_dir: Path, labels_path: Path) -> None:
        labels = json.loads(labels_path.read_text(encoding="utf-8"))
        self._answers: dict[str, ExtractedData] = {}
        for file_name, label in labels.items():
            fingerprint = hashlib.sha256(
                (samples_dir / file_name).read_bytes()
            ).hexdigest()
            self._answers[fingerprint] = ExtractedData.model_validate(label)

    def extract(self, pdf_bytes: bytes) -> ExtractedData:
        fingerprint = hashlib.sha256(pdf_bytes).hexdigest()
        try:
            return self._answers[fingerprint]
        except KeyError:
            raise ExtractionError(
                "Unknown document: not one of the evals samples"
            ) from None
