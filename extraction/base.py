"""The extractor interface. Rules only ever see an ExtractionResult, so it does not
matter whether the text came from typing, OCR, or (later) a vision model."""
from dataclasses import dataclass, field


@dataclass
class ExtractedValue:
    value: str
    confidence: float = 1.0  # typed text is certain; OCR will give lower numbers
    bbox: list | None = None  # box on the image, filled in by the OCR extractor


@dataclass
class ExtractionResult:
    raw_text: str
    fields: dict = field(default_factory=dict)  # field name -> ExtractedValue

    def get(self, name):
        """Return the ExtractedValue for a field, or None if it was not found."""
        return self.fields.get(name)


class BaseExtractor:
    def extract(self, source) -> ExtractionResult:
        raise NotImplementedError
