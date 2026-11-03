from django.test import TestCase
from django.urls import reverse

from rules.verdicts import Verdict

from .models import Scan


class PasteTextFlowTests(TestCase):
    def test_form_page_loads(self):
        self.assertEqual(self.client.get(reverse("check_text")).status_code, 200)

    def test_bad_label_is_saved_and_flagged(self):
        response = self.client.post(reverse("check_text"), {"label_text": "Just a biscuit"})
        scan = Scan.objects.get()
        self.assertRedirects(response, reverse("scan_result", args=[scan.pk]))
        self.assertEqual(scan.overall_verdict, Verdict.FAIL)
        self.assertEqual(scan.results.count(), 12)

    def test_good_label_passes_text_rules_but_needs_review(self):
        text = (
            "Product Name: Roasted Peanuts\n"
            "Manufactured by: Acme Foods Pvt Ltd, Pune 411001\n"
            "Net Wt. 250 g\nMfg: 05/2025\nBest before: 11/2025\n"
            "MRP: Rs. 120/- (Incl. of all taxes)\nUnit sale price: Rs. 0.48 per g\n"
            "Consumer care: 1800-123-4567, care@acme.in"
        )
        self.client.post(reverse("check_text"), {"label_text": text})
        scan = Scan.objects.get()
        not_passed = sorted(r.rule.code for r in scan.results.exclude(verdict=Verdict.PASS))
        # Only the measurement rules remain: letter height and panel need the image.
        self.assertEqual(not_passed, ["M01", "M02"])
        self.assertEqual(scan.overall_verdict, Verdict.CANNOT_DETERMINE)

    def test_empty_text_creates_no_scan(self):
        self.client.post(reverse("check_text"), {"label_text": "   "})
        self.assertEqual(Scan.objects.count(), 0)

    def test_result_page_shows_verdicts(self):
        self.client.post(reverse("check_text"), {"label_text": "Net Wt. 250 g"})
        scan = Scan.objects.get()
        response = self.client.get(reverse("scan_result", args=[scan.pk]))
        self.assertContains(response, "R03")
        self.assertContains(response, "Pass")
