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

    def test_good_label_passes_overall_with_pack_checks_listed(self):
        text = (
            "Product Name: Roasted Peanuts\n"
            "Manufactured by: Acme Foods Pvt Ltd, Pune 411001\n"
            "Net Wt. 250 g\nMfg: 05/2025\nBest before: 11/2025\n"
            "MRP: Rs. 120/- (Incl. of all taxes)\nUnit sale price: Rs. 0.48 per g\n"
            "Consumer care: 1800-123-4567, care@acme.in"
        )
        self.client.post(reverse("check_text"), {"label_text": text, "is_imported": "no"})
        scan = Scan.objects.get()
        not_passed = sorted(r.rule.code for r in scan.results.exclude(verdict=Verdict.PASS))
        # Only the pack checks remain open: letter height and panel need the physical pack.
        self.assertEqual(not_passed, ["M01", "M02"])
        # They are reported but not counted, so a fully compliant text can pass overall.
        self.assertEqual(scan.overall_verdict, Verdict.PASS)

    def test_unknown_import_status_keeps_r08_open(self):
        self.client.post(reverse("check_text"), {"label_text": "Net Wt. 250 g"})
        r08 = Scan.objects.get().results.get(rule__code="R08")
        self.assertEqual(r08.verdict, Verdict.CANNOT_DETERMINE)

    def test_empty_text_creates_no_scan(self):
        self.client.post(reverse("check_text"), {"label_text": "   "})
        self.assertEqual(Scan.objects.count(), 0)

    def test_result_page_shows_verdicts(self):
        self.client.post(reverse("check_text"), {"label_text": "Net Wt. 250 g"})
        scan = Scan.objects.get()
        response = self.client.get(reverse("scan_result", args=[scan.pk]))
        self.assertContains(response, "R03")
        self.assertContains(response, "Pass")


class ReportAndHistoryTests(TestCase):
    def make_scan(self, text="Net Wt. 250 g"):
        self.client.post(reverse("check_text"), {"label_text": text})
        return Scan.objects.latest("pk")

    def test_report_shows_every_check_and_the_screening_note(self):
        scan = self.make_scan()
        response = self.client.get(reverse("scan_report", args=[scan.pk]))
        self.assertEqual(response.status_code, 200)
        for code in ["R01", "R10", "M01", "M02"]:
            self.assertContains(response, code)
        self.assertContains(response, "Screening aid, not a legal determination")

    def test_report_waits_for_review(self):
        scan = Scan.objects.create(input_mode=Scan.InputMode.IMAGE)  # OCR done, not reviewed
        response = self.client.get(reverse("scan_report", args=[scan.pk]))
        self.assertRedirects(response, reverse("scan_review", args=[scan.pk]))

    def test_history_lists_scans_and_filters_by_verdict(self):
        failing = self.make_scan()
        pending = Scan.objects.create(input_mode=Scan.InputMode.IMAGE)
        response = self.client.get(reverse("scan_history"))
        self.assertContains(response, f"#{failing.pk}")
        self.assertContains(response, "Awaiting review")
        response = self.client.get(reverse("scan_history"), {"verdict": "pending"})
        self.assertContains(response, f"#{pending.pk}")
        self.assertNotContains(response, f"#{failing.pk}<")
        response = self.client.get(reverse("scan_history"), {"verdict": "FAIL"})
        self.assertNotContains(response, "Awaiting review</span>")

    def test_history_empty_state(self):
        response = self.client.get(reverse("scan_history"))
        self.assertContains(response, "No scans yet")
