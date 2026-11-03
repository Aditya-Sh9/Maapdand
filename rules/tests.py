from django.test import SimpleTestCase, TestCase

from extraction.base import ExtractedValue, ExtractionResult
from extraction.text_extractor import TextExtractor

from . import checks
from .engine import overall_verdict, run_rule
from .verdicts import Verdict


def make_result(**fields):
    """Build an ExtractionResult by hand, so rule tests don't depend on the parsers."""
    return ExtractionResult(
        raw_text="", fields={name: ExtractedValue(value) for name, value in fields.items()}
    )


class ManufacturerRuleTests(SimpleTestCase):
    def test_missing_fails(self):
        self.assertEqual(checks.check_manufacturer_details(make_result()).verdict, Verdict.FAIL)

    def test_with_pin_code_passes(self):
        result = make_result(manufacturer="Manufactured by Acme, Pune 411001")
        self.assertEqual(checks.check_manufacturer_details(result).verdict, Verdict.PASS)

    def test_without_pin_code_cannot_determine(self):
        result = make_result(manufacturer="Manufactured by Acme, Pune")
        self.assertEqual(checks.check_manufacturer_details(result).verdict, Verdict.CANNOT_DETERMINE)


class NetQuantityRuleTests(SimpleTestCase):
    def test_missing_fails(self):
        self.assertEqual(checks.check_net_quantity_declared(make_result()).verdict, Verdict.FAIL)

    def test_present_passes(self):
        result = make_result(net_quantity="Net Wt. 250 g")
        self.assertEqual(checks.check_net_quantity_declared(result).verdict, Verdict.PASS)


class ManufactureDateRuleTests(SimpleTestCase):
    def test_missing_fails(self):
        self.assertEqual(checks.check_manufacture_date(make_result()).verdict, Verdict.FAIL)

    def test_present_passes(self):
        result = make_result(mfg_date="Mfg: 05/2025")
        self.assertEqual(checks.check_manufacture_date(result).verdict, Verdict.PASS)


class MrpRuleTests(SimpleTestCase):
    def test_missing_fails(self):
        self.assertEqual(checks.check_mrp(make_result()).verdict, Verdict.FAIL)

    def test_no_rupee_sign_fails(self):
        result = make_result(mrp="MRP 120", mrp_tax_note="Incl. of all taxes")
        self.assertEqual(checks.check_mrp(result).verdict, Verdict.FAIL)

    def test_no_tax_note_fails(self):
        result = make_result(mrp="MRP Rs. 120")
        self.assertEqual(checks.check_mrp(result).verdict, Verdict.FAIL)

    def test_complete_passes(self):
        result = make_result(mrp="MRP ₹ 120", mrp_tax_note="Incl. of all taxes")
        self.assertEqual(checks.check_mrp(result).verdict, Verdict.PASS)


class OverallVerdictTests(SimpleTestCase):
    def test_any_fail_wins(self):
        self.assertEqual(overall_verdict([Verdict.PASS, Verdict.FAIL, Verdict.CANNOT_DETERMINE]), Verdict.FAIL)

    def test_doubt_beats_pass(self):
        self.assertEqual(overall_verdict([Verdict.PASS, Verdict.CANNOT_DETERMINE]), Verdict.CANNOT_DETERMINE)

    def test_all_pass(self):
        self.assertEqual(overall_verdict([Verdict.PASS, Verdict.PASS]), Verdict.PASS)

    def test_unknown_rule_code_is_cannot_determine(self):
        self.assertEqual(run_rule("R99", make_result()).verdict, Verdict.CANNOT_DETERMINE)


class EndToEndTests(SimpleTestCase):
    GOOD_LABEL = (
        "Manufactured by: Acme Foods Pvt Ltd, Plot 5, Pune 411001\n"
        "Net Wt. 250 g\nMfg: 05/2025\nMRP: Rs. 120/- (Incl. of all taxes)"
    )

    def test_good_label_passes_every_rule(self):
        result = TextExtractor().extract(self.GOOD_LABEL)
        for check in (checks.check_manufacturer_details, checks.check_net_quantity_declared,
                      checks.check_manufacture_date, checks.check_mrp):
            self.assertEqual(check(result).verdict, Verdict.PASS, check.__name__)


class SeededRulesTests(TestCase):
    def test_rules_are_seeded_by_migration(self):
        from .models import Rule
        self.assertEqual(
            sorted(Rule.objects.values_list("code", flat=True)), ["R01", "R03", "R05", "R06"]
        )
