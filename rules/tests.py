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


def verdict(check, **fields):
    return check(make_result(**fields)).verdict


class ManufactureVsPackingDateTests(SimpleTestCase):
    def test_packing_date_only_needs_review(self):
        self.assertEqual(verdict(checks.check_manufacture_date, packed_date="Packed on 05/2025"),
                         Verdict.CANNOT_DETERMINE)


class GenericNameRuleTests(SimpleTestCase):
    def test_found_passes(self):
        self.assertEqual(verdict(checks.check_generic_name, generic_name="Product Name: Peanuts"), Verdict.PASS)

    def test_missing_needs_review(self):
        self.assertEqual(verdict(checks.check_generic_name), Verdict.CANNOT_DETERMINE)


class UnitsRuleTests(SimpleTestCase):
    def check(self, text, **extra):
        return verdict(checks.check_net_quantity_units, net_quantity=text, **extra)

    def test_standard_units_pass(self):
        for text in ["Net Wt. 250 g", "Net Wt. 1.5 kg", "Net Vol. 500 ml", "Net Qty 2 L",
                     "Net Wt. 1000 g", "Net Qty 6 pcs", "शुद्ध मात्रा 500 ग्राम"]:
            self.assertEqual(self.check(text), Verdict.PASS, text)

    def test_non_si_symbol_fails(self):
        self.assertEqual(self.check("Net Wt. 200 gms"), Verdict.FAIL)
        self.assertEqual(self.check("Net Vol. 1 ltr"), Verdict.FAIL)

    def test_wrong_size_of_unit_fails(self):
        self.assertEqual(self.check("Net Wt. 0.5 kg"), Verdict.FAIL)
        self.assertEqual(self.check("Net Wt. 1500 g"), Verdict.FAIL)
        self.assertEqual(self.check("Net Vol. 2000 ml"), Verdict.FAIL)

    def test_qualifier_fails(self):
        self.assertEqual(self.check("Net Wt. 250 g", quantity_qualifier="Net Wt. approx"), Verdict.FAIL)

    def test_missing_needs_review(self):
        self.assertEqual(verdict(checks.check_net_quantity_units), Verdict.CANNOT_DETERMINE)


class ConsumerCareRuleTests(SimpleTestCase):
    def test_phone_under_heading_passes(self):
        self.assertEqual(verdict(checks.check_consumer_care, consumer_care="Customer care: 1800 123 4567",
                                 phone="1800 123 4567"), Verdict.PASS)

    def test_email_only_fails(self):
        self.assertEqual(verdict(checks.check_consumer_care, consumer_care="Customer care: a@b.in",
                                 email="a@b.in"), Verdict.FAIL)

    def test_phone_without_heading_needs_review(self):
        self.assertEqual(verdict(checks.check_consumer_care, phone="98765 43210"), Verdict.CANNOT_DETERMINE)


class CountryOfOriginRuleTests(SimpleTestCase):
    def test_unknown_import_status_needs_a_person(self):
        self.assertEqual(verdict(checks.check_country_of_origin), Verdict.CANNOT_DETERMINE)

    def test_stated_not_imported_is_not_applicable(self):
        result = make_result()
        result.is_imported = False
        self.assertEqual(checks.check_country_of_origin(result).verdict, Verdict.PASS)

    def test_stated_imported_without_origin_fails(self):
        result = make_result()
        result.is_imported = True
        self.assertEqual(checks.check_country_of_origin(result).verdict, Verdict.FAIL)

    def test_stated_imported_with_origin_passes(self):
        result = make_result(country_of_origin="Made in Thailand")
        result.is_imported = True
        self.assertEqual(checks.check_country_of_origin(result).verdict, Verdict.PASS)

    def test_imported_without_origin_fails(self):
        self.assertEqual(verdict(checks.check_country_of_origin, import_statement="Imported by"), Verdict.FAIL)

    def test_imported_with_origin_passes(self):
        self.assertEqual(verdict(checks.check_country_of_origin, import_statement="Imported by",
                                 country_of_origin="Country of Origin: Thailand"), Verdict.PASS)


class UnitSalePriceRuleTests(SimpleTestCase):
    def check(self, quantity, usp=None):
        fields = {"net_quantity": quantity}
        if usp:
            fields["unit_sale_price"] = usp
        return verdict(checks.check_unit_sale_price, **fields)

    def test_right_base_passes(self):
        self.assertEqual(self.check("Net Wt. 250 g", "₹ 0.48 per g"), Verdict.PASS)
        self.assertEqual(self.check("Net Wt. 5 kg", "Rs. 52.00 per kg"), Verdict.PASS)
        self.assertEqual(self.check("Net Wt. 1 kg", "Rs. 0.10 per g"), Verdict.PASS)  # exactly 1 kg: either
        self.assertEqual(self.check("Net Qty 6 pcs", "₹ 10 per piece"), Verdict.PASS)

    def test_wrong_base_fails(self):
        self.assertEqual(self.check("Net Wt. 250 g", "₹ 480 per kg"), Verdict.FAIL)
        self.assertEqual(self.check("Net Wt. 5 kg", "₹ 0.05 per g"), Verdict.FAIL)
        self.assertEqual(self.check("Net Wt. 250 g", "₹ 48 per 100 g"), Verdict.FAIL)
        self.assertEqual(self.check("Net Wt. 250 g", "₹ 0.48 per ml"), Verdict.FAIL)

    def test_missing_fails_unless_single_item(self):
        self.assertEqual(self.check("Net Wt. 250 g"), Verdict.FAIL)
        self.assertEqual(self.check("Net Qty 1 N"), Verdict.PASS)


class BestBeforeRuleTests(SimpleTestCase):
    def test_found_passes(self):
        self.assertEqual(verdict(checks.check_best_before, best_before="Best before 11/2026"), Verdict.PASS)

    def test_missing_needs_review(self):
        self.assertEqual(verdict(checks.check_best_before), Verdict.CANNOT_DETERMINE)


class MeasurementRuleTests(SimpleTestCase):
    def test_always_needs_review(self):
        for check in (checks.check_letter_height, checks.check_principal_display_panel):
            self.assertEqual(verdict(check), Verdict.CANNOT_DETERMINE)


class OverallVerdictScopeTests(TestCase):
    """M01/M02 need the physical pack, so they are shown but left out of the overall verdict."""

    def test_pack_rules_are_flagged(self):
        from .models import Rule
        self.assertEqual(sorted(Rule.objects.filter(needs_pack=True).values_list("code", flat=True)), ["M01", "M02"])

    def test_label_that_passes_every_text_rule_can_pass_overall(self):
        from unittest import mock
        from scans.models import Scan
        from .engine import run_scan
        from .verdicts import RuleOutcome
        always_pass = mock.Mock(return_value=RuleOutcome(Verdict.PASS, "ok"))
        with mock.patch("rules.engine.run_rule", side_effect=lambda code, r: always_pass() if not code.startswith("M")
                        else RuleOutcome(Verdict.CANNOT_DETERMINE, "needs the pack")):
            scan = run_scan(Scan.objects.create(), make_result())
        self.assertEqual(scan.overall_verdict, Verdict.PASS)
        self.assertEqual(scan.results.filter(verdict=Verdict.CANNOT_DETERMINE).count(), 2)  # still recorded


class SeededRulesTests(TestCase):
    def test_rules_are_seeded_by_migration(self):
        from .models import Rule
        self.assertEqual(
            sorted(Rule.objects.values_list("code", flat=True)),
            ["M01", "M02", "R01", "R02", "R03", "R04", "R05", "R06", "R07", "R08", "R09", "R10"],
        )

    def test_no_reference_left_unverified(self):
        from .models import Rule
        self.assertFalse(Rule.objects.filter(legal_reference__icontains="verify").exists())
