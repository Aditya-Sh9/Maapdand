import os
import tempfile
import unittest

from django.conf import settings
from django.test import SimpleTestCase
from PIL import Image, ImageDraw, ImageFont

from .ocr_extractor import OCRExtractor, locate
from .preprocess import assess_quality, preprocess

TESSERACT_AVAILABLE = os.path.exists(settings.TESSERACT_CMD) and os.path.exists(
    settings.TESSDATA_DIR / "eng.traineddata"
)


def make_label_image(path, lines, size=(1800, 500)):
    """Draw black text on white, like a clean scan of a label."""
    font = ImageFont.truetype(r"C:\Windows\Fonts\arial.ttf", 44)
    img = Image.new("RGB", size, "white")
    draw = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        draw.text((40, 30 + i * 90), line, fill="black", font=font)
    img.save(path)


class QualityTests(SimpleTestCase):
    def test_sharp_large_image_is_ok(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "a.png")
            make_label_image(path, ["Net Quantity: 500 g", "MRP Rs. 45.00"])
            score, ok, reasons = assess_quality(Image.open(path))
        self.assertTrue(ok, reasons)

    def test_tiny_image_is_rejected(self):
        _, ok, reasons = assess_quality(Image.new("RGB", (100, 100), "white"))
        self.assertFalse(ok)
        self.assertIn("Image resolution is too low.", reasons)

    def test_blank_image_counts_as_blurry(self):
        _, ok, reasons = assess_quality(Image.new("RGB", (1500, 1500), "white"))
        self.assertIn("Image looks blurry.", reasons)

    def test_preprocess_enlarges_small_images_to_grayscale(self):
        out = preprocess(Image.new("RGB", (500, 250), "white"))
        self.assertEqual(out.mode, "L")
        self.assertEqual(out.width, 2000)


class LocateTests(SimpleTestCase):
    WORDS = [
        {"text": "MRP:", "conf": 0.9, "box": (10, 10, 40, 20), "line": (1, 1, 1)},
        {"text": "Rs.", "conf": 0.8, "box": (60, 10, 30, 20), "line": (1, 1, 1)},
        {"text": "45.00", "conf": 0.7, "box": (100, 10, 50, 20), "line": (1, 1, 1)},
    ]

    def test_box_covers_matching_words_as_fractions(self):
        bbox, confidence = locate("MRP Rs. 45.00", self.WORDS, (200, 100))
        self.assertEqual(bbox, [0.05, 0.1, 0.7, 0.2])
        self.assertAlmostEqual(confidence, 0.8)

    def test_no_match_gives_none(self):
        self.assertEqual(locate("Net Wt", self.WORDS, (200, 100)), (None, None))


@unittest.skipUnless(TESSERACT_AVAILABLE, "Tesseract or its language data is not installed")
class OCRExtractorTests(SimpleTestCase):
    def test_reads_fields_from_two_images_of_one_product(self):
        with tempfile.TemporaryDirectory() as tmp:
            front = os.path.join(tmp, "front.png")
            back = os.path.join(tmp, "back.png")
            make_label_image(front, ["Net Quantity: 500 g"])
            make_label_image(back, ["MRP Rs. 45.00 (Inclusive of all taxes)"])
            result = OCRExtractor().extract([front, back])

        self.assertEqual(len(result.image_texts), 2)
        # Each field is found in a different image, and both count.
        self.assertEqual(result.fields["net_quantity"].image_index, 0)
        self.assertEqual(result.fields["mrp"].image_index, 1)
        self.assertIn("500", result.fields["net_quantity"].value)
        self.assertIsNotNone(result.fields["mrp"].bbox)

    @unittest.skipUnless(
        os.path.exists(settings.TESSDATA_DIR / "hin.traineddata")
        and os.path.exists(r"C:\Windows\Fonts\Nirmala.ttc"),
        "Hindi language data or a Devanagari font is missing",
    )
    def test_reads_a_hindi_label(self):
        font = ImageFont.truetype(r"C:\Windows\Fonts\Nirmala.ttc", 48)
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "hindi.png")
            img = Image.new("RGB", (1800, 400), "white")
            draw = ImageDraw.Draw(img)
            draw.text((40, 40), "शुद्ध मात्रा: 500 ग्राम", fill="black", font=font)
            draw.text((40, 160), "अधिकतम खुदरा मूल्य ₹ 45.00", fill="black", font=font)
            img.save(path)
            result = OCRExtractor().extract([path])
        # Hindi OCR is weaker than English, so only check that Devanagari came back
        # and that the digits survived.
        self.assertRegex(result.raw_text, r"[\u0900-\u097F]")
        self.assertIn("500", result.raw_text)
        print("\nHindi OCR read:", result.raw_text.replace("\n", " | "), "->", sorted(result.fields))
