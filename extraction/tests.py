from django.test import SimpleTestCase

from . import parsers
from .text_extractor import TextExtractor


class ParserTests(SimpleTestCase):
    def test_devanagari_digits_become_ascii(self):
        self.assertEqual(parsers.normalize_text("₹ १२०"), "₹ 120")

    def test_net_quantity_variants(self):
        self.assertEqual(parsers.find_net_quantity("Net Wt. 250 g"), "Net Wt. 250 g")
        self.assertEqual(parsers.find_net_quantity("NET QTY: 1.5L"), "NET QTY: 1.5L")
        self.assertEqual(parsers.find_net_quantity("Net Content 500ml"), "Net Content 500ml")

    def test_net_quantity_needs_keyword_and_unit(self):
        self.assertIsNone(parsers.find_net_quantity("250 g of goodness"))
        self.assertIsNone(parsers.find_net_quantity("Net Weight: lots"))

    def test_mfg_date_variants(self):
        self.assertIsNotNone(parsers.find_mfg_date("Mfg: 05/2025"))
        self.assertIsNotNone(parsers.find_mfg_date("Mfd. Date 12/05/2025"))
        self.assertIsNotNone(parsers.find_mfg_date("Packed on: MAY 2025"))
        self.assertIsNotNone(parsers.find_mfg_date("Mfg Date: Jan-25"))

    def test_mfg_date_missing(self):
        self.assertIsNone(parsers.find_mfg_date("Best before 6 months"))

    def test_mrp_variants(self):
        self.assertEqual(parsers.find_mrp("MRP: Rs. 120/-"), "MRP: Rs. 120")
        self.assertEqual(parsers.find_mrp("M.R.P. ₹ 99.50"), "M.R.P. ₹ 99.50")
        self.assertIsNotNone(parsers.find_mrp("MRP (Incl. of all taxes) Rs 45"))

    def test_mrp_hindi(self):
        self.assertIsNotNone(parsers.find_mrp("अधिकतम खुदरा मूल्य ₹ 120"))

    def test_mrp_missing(self):
        self.assertIsNone(parsers.find_mrp("Price on request"))

    def test_tax_note(self):
        self.assertIsNotNone(parsers.find_mrp_tax_note("Incl. of all taxes"))
        self.assertIsNotNone(parsers.find_mrp_tax_note("inclusive of all taxes"))
        self.assertIsNone(parsers.find_mrp_tax_note("plus taxes extra"))

    def test_manufacturer(self):
        found = parsers.find_manufacturer("Manufactured by: Acme Foods Pvt Ltd, Pune 411001")
        self.assertIn("Acme Foods", found)
        self.assertTrue(parsers.has_pin_code(found))

    def test_manufacturer_not_confused_with_date(self):
        self.assertIsNone(parsers.find_manufacturer("Mfd: 05/2025"))

    def test_pin_code(self):
        self.assertFalse(parsers.has_pin_code("Pune 4110"))


class TextExtractorTests(SimpleTestCase):
    def test_extracts_only_found_fields(self):
        result = TextExtractor().extract("Net Wt. 250 g\nMRP Rs. 50")
        self.assertIsNotNone(result.get("net_quantity"))
        self.assertIsNotNone(result.get("mrp"))
        self.assertIsNone(result.get("mfg_date"))

    def test_hindi_digits_in_text(self):
        result = TextExtractor().extract("MRP ₹ १२०")
        self.assertIn("120", result.get("mrp").value)
