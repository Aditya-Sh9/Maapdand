import io
import shutil
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from extraction.base import ExtractedValue, ExtractionResult
from extraction.test_ocr import make_label_image
from rules.verdicts import Verdict

from .models import ExtractedField, LabelImage, Product, Scan
from .services import apply_review_and_run

TEMP_MEDIA = tempfile.mkdtemp()


def png_upload(lines, name="label.png"):
    """A fake uploaded photo made of the given text lines."""
    buffer = io.BytesIO()
    path = tempfile.mktemp(suffix=".png")
    make_label_image(path, lines)
    Image.open(path).save(buffer, format="PNG")
    return SimpleUploadedFile(name, buffer.getvalue(), content_type="image/png")


class FakeOCR:
    """Stands in for Tesseract so these tests are fast and do not need it installed."""

    def extract(self, paths):
        fields = {
            "net_quantity": ExtractedValue("Net Quantity: 5O0 g", 0.6, [0, 0, 0.5, 0.1], 0),
        }
        return ExtractionResult(raw_text="Net Quantity: 5O0 g", fields=fields, image_texts=["Net Quantity: 5O0 g"])


@override_settings(MEDIA_ROOT=TEMP_MEDIA)
class ImageFlowTests(TestCase):
    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(TEMP_MEDIA, ignore_errors=True)
        super().tearDownClass()

    def upload(self, **extra):
        data = {"images": [png_upload(["Net Quantity: 500 g", "MRP Rs. 45.00"])], "category": "food"}
        data.update(extra)
        return self.client.post(reverse("upload_images"), data)

    def test_upload_page_loads(self):
        self.assertEqual(self.client.get(reverse("upload_images")).status_code, 200)

    def test_no_files_is_rejected(self):
        response = self.client.post(reverse("upload_images"), {"category": "food"})
        self.assertContains(response, "Choose at least one image.")
        self.assertEqual(Scan.objects.count(), 0)

    def test_tiny_image_stops_at_the_quality_gate(self):
        tiny = io.BytesIO()
        Image.new("RGB", (100, 100), "white").save(tiny, format="PNG")
        upload = SimpleUploadedFile("tiny.png", tiny.getvalue(), content_type="image/png")
        response = self.client.post(reverse("upload_images"), {"images": [upload]})
        self.assertContains(response, "resolution is too low")
        self.assertEqual(Product.objects.count(), 0)

    def test_non_image_file_is_rejected(self):
        junk = SimpleUploadedFile("notes.png", b"not an image", content_type="image/png")
        response = self.client.post(reverse("upload_images"), {"images": [junk]})
        self.assertContains(response, "could not be read as an image")

    def test_upload_saves_product_and_goes_to_review_without_a_verdict(self):
        from unittest import mock
        with mock.patch("scans.services.OCRExtractor", FakeOCR):
            response = self.upload()
        scan = Scan.objects.get()
        self.assertRedirects(response, reverse("scan_review", args=[scan.pk]))
        self.assertEqual(scan.product.category, "food")
        self.assertEqual(LabelImage.objects.filter(product=scan.product).count(), 1)
        self.assertEqual(scan.overall_verdict, "")  # no verdict until a human reviews
        self.assertEqual(scan.results.count(), 0)
        self.assertEqual(scan.fields.get().source_image.product, scan.product)

    def test_unreviewed_result_redirects_to_review(self):
        scan = Scan.objects.create(input_mode=Scan.InputMode.IMAGE)
        response = self.client.get(reverse("scan_result", args=[scan.pk]))
        self.assertRedirects(response, reverse("scan_review", args=[scan.pk]))

    def test_review_page_lists_every_field(self):
        scan = Scan.objects.create(input_mode=Scan.InputMode.IMAGE)
        ExtractedField.objects.create(scan=scan, field_name="mrp", value="MRP Rs. 45", confidence=0.8)
        response = self.client.get(reverse("scan_review", args=[scan.pk]))
        self.assertContains(response, 'name="field_mrp"')
        self.assertContains(response, 'name="field_net_quantity"')
        self.assertContains(response, "Not found")

    def test_review_corrections_are_used_by_the_rules(self):
        scan = Scan.objects.create(input_mode=Scan.InputMode.IMAGE, raw_text="x")
        ExtractedField.objects.create(scan=scan, field_name="net_quantity", value="Net Quantity: 5O0 g")
        apply_review_and_run(scan, {
            "net_quantity": "Net Quantity: 500 g",
            "mrp": "MRP Rs. 45.00",
            "mrp_tax_note": "Inclusive of all taxes",
        })
        scan.refresh_from_db()

        ocr_field = scan.fields.get(field_name="net_quantity")
        self.assertEqual(ocr_field.value, "Net Quantity: 5O0 g")  # original kept
        self.assertEqual(ocr_field.final_value, "Net Quantity: 500 g")
        self.assertEqual(scan.fields.get(field_name="mrp").final_value, "MRP Rs. 45.00")
        self.assertEqual(scan.results.get(rule__code="R03").verdict, Verdict.PASS)
        self.assertEqual(scan.results.get(rule__code="R06").verdict, Verdict.PASS)

    def test_reviewing_twice_replaces_old_results(self):
        scan = Scan.objects.create(input_mode=Scan.InputMode.IMAGE, raw_text="x")
        apply_review_and_run(scan, {})
        apply_review_and_run(scan, {"net_quantity": "Net Wt. 250 g"})
        self.assertEqual(scan.results.count(), 12)

    def test_review_post_redirects_to_result(self):
        scan = Scan.objects.create(input_mode=Scan.InputMode.IMAGE, raw_text="x")
        response = self.client.post(reverse("scan_review", args=[scan.pk]), {"field_mrp": "MRP Rs. 45.00"})
        self.assertRedirects(response, reverse("scan_result", args=[scan.pk]))
        scan.refresh_from_db()
        self.assertNotEqual(scan.overall_verdict, "")
