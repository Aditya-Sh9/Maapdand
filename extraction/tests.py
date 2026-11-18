from decimal import Decimal

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
        self.assertIsNotNone(parsers.find_mfg_date("Mfg Date: Jan-25"))
        self.assertIsNotNone(parsers.find_mfg_date("Mfg./Pkd. Date: 05/2025"))

    def test_packing_date_is_not_a_manufacture_date(self):
        self.assertIsNone(parsers.find_mfg_date("Packed on: MAY 2025"))
        self.assertIsNotNone(parsers.find_packed_date("Packed on: MAY 2025"))

    def test_quantity_qualifier(self):
        self.assertIsNotNone(parsers.find_quantity_qualifier("Net Wt. approx. 250 g"))
        self.assertIsNotNone(parsers.find_quantity_qualifier("Net Qty (Minimum) 1 kg"))
        self.assertIsNone(parsers.find_quantity_qualifier("Net Wt. 250 g"))

    def test_split_unit_sale_price(self):
        self.assertEqual(parsers.split_unit_sale_price("Unit Sale Price: ₹ 0.48/g"),
                         (Decimal("0.48"), Decimal(1), "g"))
        self.assertEqual(parsers.split_unit_sale_price("USP Rs. 48 per 100 g"),
                         (Decimal("48"), Decimal("100"), "g"))

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

    def test_hindi_mrp_survives_an_ocr_slip_in_the_first_word(self):
        self.assertIn("45.00", parsers.find_mrp("अधकितम खुदरा मूल्य ₹ 45.00"))
        self.assertIn("45.00", parsers.find_mrp("अधिकतम खुदरा मूल्य ₹ 45.00"))

    def test_manufacturer_stops_at_next_labelled_line(self):
        text = "Marketed by: Sunrise Foods, 12 MG Road, Pune 411001\nNet Quantity: 500 g\nMRP Rs. 45"
        found = parsers.find_manufacturer(text)
        self.assertTrue(found.endswith("411001"))
        self.assertNotIn("Net Quantity", found)

    def test_manufacturer_keeps_a_two_line_address(self):
        text = "Manufactured by: Acme Foods Pvt Ltd\n12 Industrial Area, Pune 411001\n\nMRP Rs. 45"
        found = parsers.find_manufacturer(text)
        self.assertIn("Industrial Area", found)
        self.assertTrue(parsers.has_pin_code(found))

    def test_bare_product_label_is_a_generic_name(self):
        self.assertEqual(parsers.find_generic_name("Product: Wheat Flour"), "Product: Wheat Flour")

    def test_product_of_india_is_not_a_generic_name(self):
        self.assertIsNone(parsers.find_generic_name("Product of India"))

    def test_pin_code(self):
        self.assertFalse(parsers.has_pin_code("Pune 4110"))

    def test_net_quantity_hindi(self):
        self.assertIsNotNone(parsers.find_net_quantity("शुद्ध मात्रा 500 ग्राम"))
        self.assertIsNotNone(parsers.find_net_quantity("निवल मात्रा: 1 किग्रा"))

    def test_split_quantity(self):
        self.assertEqual(parsers.split_quantity("Net Wt. 1,000 g"), (Decimal("1000"), "g"))
        self.assertEqual(parsers.split_quantity("NET QTY: 1.5L"), (Decimal("1.5"), "l"))
        self.assertEqual(parsers.split_quantity("Net Wt 200 gms"), (Decimal("200"), "gms"))
        self.assertIsNone(parsers.split_quantity("Net Weight: lots"))

    def test_generic_name(self):
        self.assertEqual(parsers.find_generic_name("Product Name: Roasted Peanuts\nMRP 50"),
                         "Product Name: Roasted Peanuts")
        self.assertIsNotNone(parsers.find_generic_name("उत्पाद का नाम: मूंगफली"))
        self.assertIsNone(parsers.find_generic_name("Roasted Peanuts"))

    def test_best_before_date_and_duration(self):
        self.assertIsNotNone(parsers.find_best_before("Best Before: 11/2026"))
        self.assertIsNotNone(parsers.find_best_before("EXP. DATE MAR 2027"))
        found = parsers.find_best_before("Best before 6 months from manufacture")
        self.assertEqual(found, "Best before 6 months from manufacture")
        self.assertIsNotNone(parsers.find_best_before("उपयोग की अंतिम तिथि 05/2026"))

    def test_best_before_missing(self):
        self.assertIsNone(parsers.find_best_before("Mfg: 05/2025"))
        self.assertIsNone(parsers.find_best_before("Best before eating, shake well"))

    def test_unit_sale_price(self):
        self.assertIsNotNone(parsers.find_unit_sale_price("Unit Sale Price: ₹ 0.48/g"))
        self.assertIsNotNone(parsers.find_unit_sale_price("USP Rs. 48 per 100 g"))
        self.assertIsNotNone(parsers.find_unit_sale_price("(₹ 240 per kg)"))
        self.assertIsNotNone(parsers.find_unit_sale_price("इकाई विक्रय मूल्य ₹ 2.40 प्रति ग्राम"))

    def test_unit_sale_price_not_mrp_or_bare_ratio(self):
        self.assertIsNone(parsers.find_unit_sale_price("MRP Rs. 120/- incl. of all taxes"))
        self.assertIsNone(parsers.find_unit_sale_price("250/g"))

    def test_consumer_care(self):
        found = parsers.find_consumer_care("Consumer Care: 1800-123-4567, care@acme.in")
        self.assertIn("1800-123-4567", found)
        self.assertIsNotNone(parsers.find_consumer_care("उपभोक्ता सेवा हेतु संपर्क करें"))

    def test_email(self):
        self.assertEqual(parsers.find_email("write to care@acme.co.in today"), "care@acme.co.in")
        self.assertIsNone(parsers.find_email("care at acme dot in"))

    def test_phone_formats(self):
        self.assertIsNotNone(parsers.find_phone("Call 98765 43210"))
        self.assertIsNotNone(parsers.find_phone("+91-9876543210"))
        self.assertIsNotNone(parsers.find_phone("Toll free 1800 123 4567"))
        self.assertIsNotNone(parsers.find_phone("Tel: 022-12345678"))

    def test_phone_ignores_barcode_and_pin(self):
        self.assertIsNone(parsers.find_phone("8901234567890"))  # 13-digit EAN barcode
        self.assertIsNone(parsers.find_phone("Pune 411001"))

    def test_import_statement(self):
        self.assertIsNotNone(parsers.find_import_statement("Imported by: XYZ Traders, Delhi"))
        self.assertIsNotNone(parsers.find_import_statement("आयातक: XYZ"))
        self.assertIsNone(parsers.find_import_statement("Manufactured by Acme"))

    def test_country_of_origin(self):
        self.assertEqual(parsers.find_country_of_origin("Country of Origin: Thailand\nMRP 50"),
                         "Country of Origin: Thailand")
        # Dots are kept in the value so "U.S.A." survives; a trailing "." is harmless.
        self.assertIn("Made in China", parsers.find_country_of_origin("Made in China."))
        self.assertIsNotNone(parsers.find_country_of_origin("मूल देश: भारत"))
        self.assertIsNone(parsers.find_country_of_origin("Imported by XYZ"))


class TextExtractorTests(SimpleTestCase):
    def test_extracts_only_found_fields(self):
        result = TextExtractor().extract("Net Wt. 250 g\nMRP Rs. 50")
        self.assertIsNotNone(result.get("net_quantity"))
        self.assertIsNotNone(result.get("mrp"))
        self.assertIsNone(result.get("mfg_date"))

    def test_hindi_digits_in_text(self):
        result = TextExtractor().extract("MRP ₹ १२०")
        self.assertIn("120", result.get("mrp").value)
