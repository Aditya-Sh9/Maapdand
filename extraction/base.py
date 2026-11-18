"""The extractor interface. Rules only ever see an ExtractionResult, so it does not
matter whether the text came from typing, OCR, or (later) a vision model."""
from dataclasses import dataclass, field


@dataclass
class ExtractedValue:
    value: str
    confidence: float = 1.0  # typed text is certain; OCR will give lower numbers
    # Box on the image as fractions of its size: [left, top, width, height], each 0..1.
    # Fractions (not pixels) so it still fits when the image is shown at any size.
    bbox: list | None = None
    image_index: int | None = None  # which input image it came from (None for typed text)


@dataclass
class ExtractionResult:
    raw_text: str
    fields: dict = field(default_factory=dict)  # field name -> ExtractedValue
    image_texts: list = field(default_factory=list)  # OCR text of each input image, in order

    def get(self, name):
        """Return the ExtractedValue for a field, or None if it was not found."""
        return self.fields.get(name)


class BaseExtractor:
    def extract(self, source) -> ExtractionResult:
        raise NotImplementedError
