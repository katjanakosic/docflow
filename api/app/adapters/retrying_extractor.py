"""An extractor that gives another extractor several attempts before giving up."""

import logging
import time
from collections.abc import Callable, Sequence

from app.domain.models import ExtractedData
from app.domain.ports import ExtractionError, Extractor

logger = logging.getLogger(__name__)


class RetryingExtractor:
    def __init__(
        self,
        inner: Extractor,
        delays: Sequence[float] = (10, 40),
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._inner = inner
        self._delays = delays  # seconds to wait after each failed attempt but the last
        self._sleep = sleep

    def extract(self, pdf_bytes: bytes) -> ExtractedData:
        for attempt, delay in enumerate(self._delays, start=1):
            try:
                return self._inner.extract(pdf_bytes)
            except ExtractionError as error:
                logger.warning(
                    "Attempt %d failed (%s); retrying in %ss", attempt, error, delay
                )
                self._sleep(delay)

        try:
            return self._inner.extract(pdf_bytes)  # the last attempt
        except ExtractionError as error:
            attempts = len(self._delays) + 1
            raise ExtractionError(
                f"Failed after {attempts} attempts: {error}"
            ) from error
