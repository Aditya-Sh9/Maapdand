"""Glue between the pieces: text in -> extract -> save -> run rules -> saved Scan."""
from extraction.text_extractor import TextExtractor
from rules.engine import run_scan

from .models import ExtractedField, Scan


def run_text_scan(text, user=None):
    result = TextExtractor().extract(text)
    scan = Scan.objects.create(
        input_mode=Scan.InputMode.TEXT,
        raw_text=result.raw_text,
        created_by=user if user and user.is_authenticated else None,
    )
    for name, extracted in result.fields.items():
        ExtractedField.objects.create(
            scan=scan, field_name=name, value=extracted.value, confidence=extracted.confidence
        )
    return run_scan(scan, result)
