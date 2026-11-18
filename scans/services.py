"""Glue between the pieces. Two flows:

Text:  text -> extract -> save -> run rules                      (run_text_scan)
Image: upload -> quality check -> OCR -> save -> [human review] -> run rules
       (create_image_scan, then apply_review_and_run)
"""
from django.db import transaction

from extraction.base import ExtractedValue, ExtractionResult
from extraction.ocr_extractor import OCRExtractor
from extraction.preprocess import assess_quality, load_image
from extraction.text_extractor import FIELD_NAMES, TextExtractor
from rules.engine import run_scan

from .models import ExtractedField, LabelImage, Product, Scan


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


def check_image_quality(uploaded_file):
    """Quality check for one uploaded file. Returns (score, ok, reasons).
    A file Pillow cannot open is reported as bad rather than crashing."""
    try:
        img = load_image(uploaded_file)
        score, ok, reasons = assess_quality(img)
    except Exception:  # not an image, truncated, unsupported format...
        return 0.0, False, ["This file could not be read as an image."]
    uploaded_file.seek(0)  # Pillow read the file; rewind so Django can save it
    return score, ok, reasons


@transaction.atomic
def create_image_scan(files, category="", name="", is_imported=None, user=None):
    """Save the product and its images, OCR them, and store what was found.
    No rules run yet: the person reviews and corrects the fields first."""
    owner = user if user and user.is_authenticated else None
    product = Product.objects.create(
        name=name, category=category, is_imported=is_imported, created_by=owner
    )
    images = []
    for f in files:
        score, ok, _ = check_image_quality(f)
        images.append(
            LabelImage.objects.create(product=product, image=f, quality_score=score, quality_ok=ok)
        )

    result = OCRExtractor().extract([img.image.path for img in images])
    for img, text in zip(images, result.image_texts):
        img.ocr_text = text
        img.save(update_fields=["ocr_text"])

    scan = Scan.objects.create(
        product=product, input_mode=Scan.InputMode.IMAGE, raw_text=result.raw_text, created_by=owner
    )
    for field_name, found in result.fields.items():
        ExtractedField.objects.create(
            scan=scan, field_name=field_name, value=found.value,
            confidence=found.confidence, bbox=found.bbox,
            source_image=images[found.image_index],
        )
    return scan


def result_from_fields(scan):
    """Rebuild the ExtractionResult the rules expect from the saved (possibly corrected) fields."""
    fields = {}
    for f in scan.fields.all():
        if f.final_value:
            fields[f.field_name] = ExtractedValue(
                value=f.final_value, confidence=f.confidence, bbox=f.bbox
            )
    return ExtractionResult(raw_text=scan.raw_text, fields=fields)


@transaction.atomic
def apply_review_and_run(scan, corrections):
    """`corrections` maps field name -> the text the reviewer wants (may equal the OCR value).
    Saves differences, then runs every rule on the final values. Safe to repeat."""
    existing = {f.field_name: f for f in scan.fields.all()}
    for name, text in corrections.items():
        text = text.strip()
        field = existing.get(name)
        if field is None:
            if text:  # the reviewer typed a value OCR never found
                ExtractedField.objects.create(
                    scan=scan, field_name=name, value="", corrected_value=text, confidence=1.0
                )
            continue
        field.corrected_value = "" if text == field.value else text
        field.save(update_fields=["corrected_value"])

    scan.results.all().delete()  # a second review replaces the first verdicts
    return run_scan(scan, result_from_fields(scan))


# Plain names for the field keys, shown on the review and result pages.
FIELD_LABELS = {
    "manufacturer": "Manufacturer / packer / importer",
    "import_statement": "Imported by",
    "generic_name": "Common or generic name",
    "net_quantity": "Net quantity",
    "quantity_qualifier": "Quantity qualifier (approx., min.)",
    "mfg_date": "Month and year of manufacture",
    "packed_date": "Packing date",
    "best_before": "Best before / use by",
    "mrp": "MRP",
    "mrp_tax_note": "“Inclusive of all taxes” note",
    "unit_sale_price": "Unit sale price",
    "consumer_care": "Consumer care details",
    "email": "Email",
    "phone": "Phone",
    "country_of_origin": "Country of origin",
}
# A few rule functions name their evidence differently from the field it came from.
EVIDENCE_TO_FIELD = {"tax_note": "mrp_tax_note"}
LOW_CONFIDENCE = 0.6  # below this the review page asks the person to double-check


def field_label(name):
    return FIELD_LABELS.get(name, name.replace("_", " ").capitalize())


def image_index_map(scan):
    """LabelImage id -> position (0, 1, 2...) in the product's image list."""
    if not scan.product:
        return {}
    return {img.pk: i for i, img in enumerate(scan.product.images.all())}


def review_rows(scan):
    """One row per known field for the review page, found fields first, then missing ones.
    Each row carries what the template needs: label, value, confidence and where it was seen."""
    existing = {f.field_name: f for f in scan.fields.all()}
    positions = image_index_map(scan)
    found, missing = [], []
    for name in FIELD_NAMES:
        field = existing.get(name)
        row = {"name": name, "label": field_label(name), "field": field}
        if field and field.final_value:
            row.update(
                value=field.final_value,
                confidence=round(field.confidence * 100),
                low=field.confidence < LOW_CONFIDENCE,
                bbox=field.bbox,
                image_index=positions.get(field.source_image_id),
            )
            found.append(row)
        else:
            missing.append(row)
    return found, missing


def result_rows(scan, rule_order):
    """Rule results for the result page, in R01..R10, M01..M02 order, each with readable
    evidence and the image boxes the evidence came from."""
    fields = {f.field_name: f for f in scan.fields.all()}
    positions = image_index_map(scan)
    rows = []
    for result in sorted(scan.results.select_related("rule"), key=lambda r: rule_order(r.rule)):
        evidence, boxes = [], []
        for key, value in (result.evidence or {}).items():
            name = EVIDENCE_TO_FIELD.get(key, key)
            evidence.append({"label": field_label(name), "value": value})
            field = fields.get(name)
            if field and field.bbox and field.source_image_id in positions:
                boxes.append({"image": positions[field.source_image_id], "bbox": field.bbox, "field": name})
        rows.append({"result": result, "rule": result.rule, "evidence": evidence, "boxes": boxes})
    return rows


def verdict_summary(rows):
    """Counts per verdict plus the donut segments (an SVG circle with r=60)."""
    from rules.verdicts import Verdict

    total = len(rows)
    counts = {v: sum(1 for r in rows if r["result"].verdict == v) for v in Verdict.values}
    circumference = 2 * 3.14159265 * 60
    segments, offset = [], 0.0
    for verdict, css in [(Verdict.FAIL, "fail"), (Verdict.CANNOT_DETERMINE, "cannot"), (Verdict.PASS, "pass")]:
        length = circumference * counts[verdict] / total if total else 0
        if length:
            segments.append({"css": css, "dash": f"{length:.2f} {circumference:.2f}", "offset": f"{-offset:.2f}"})
        offset += length
    return {
        "total": total,
        "passed": counts[Verdict.PASS],
        "failed": counts[Verdict.FAIL],
        "cannot": counts[Verdict.CANNOT_DETERMINE],
        "attention": counts[Verdict.FAIL] + counts[Verdict.CANNOT_DETERMINE],  # what an officer should look at
        "segments": segments,
        "circumference": f"{circumference:.2f}",
    }
