import io
import tempfile
from pathlib import Path

from django.core.management import call_command
from django.core.management.base import CommandError
from django.test import SimpleTestCase, TestCase

from .dataset import DatasetError, load_cases
from .runner import Score


def write_csv(folder, body, files=("a.txt",)):
    for name in files:
        (Path(folder) / name).write_text("Net Wt. 200 g", encoding="utf-8")
    path = Path(folder) / "cases.csv"
    path.write_text("id,input,is_imported,synthetic,notes,R03\n" + body, encoding="utf-8")
    return path


class DatasetTests(SimpleTestCase):
    def test_starter_set_loads(self):
        cases = load_cases()
        self.assertGreaterEqual(len(cases), 20)
        self.assertTrue(all(c.expected for c in cases))
        self.assertIn("image", {c.kind for c in cases})

    def test_reads_answers_and_blank_cells(self):
        with tempfile.TemporaryDirectory() as folder:
            case = load_cases(write_csv(folder, "c1,a.txt,yes,no,,\n"))[0]
        self.assertIs(case.is_imported, True)
        self.assertFalse(case.synthetic)
        self.assertEqual(case.expected, {})  # blank cell = not labelled, not scored

    def test_bad_verdict_names_the_line(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesMessage(DatasetError, "line 2"):
                load_cases(write_csv(folder, "c1,a.txt,no,yes,,MAYBE\n"))

    def test_missing_file_is_reported(self):
        with tempfile.TemporaryDirectory() as folder:
            with self.assertRaisesMessage(DatasetError, "file not found"):
                load_cases(write_csv(folder, "c1,missing.txt,no,yes,,PASS\n"))


class ScoreTests(SimpleTestCase):
    def test_error_kinds_are_counted_separately(self):
        s = Score()
        s.add("a", "FAIL", "FAIL")
        s.add("b", "FAIL", "PASS")              # missed violation
        s.add("c", "PASS", "FAIL")              # false alarm
        s.add("d", "PASS", "CANNOT_DETERMINE")  # sent to a person
        s.add("e", "CANNOT_DETERMINE", "PASS")  # overreach
        self.assertEqual((s.correct, s.missed, s.false_alarm, s.deferred, s.overreach), (1, 1, 1, 1, 1))
        self.assertAlmostEqual(s.accuracy, 0.2)


class EvaluateCommandTests(TestCase):
    def test_runs_text_cases_and_reports_missed_violations(self):
        out = io.StringIO()
        call_command("evaluate", "--only", "text", stdout=out)
        report = out.getvalue()
        self.assertIn("Overall verdict", report)
        self.assertIn("Missed violations (expected Fail, got Pass): **0**", report)

    def test_bad_csv_is_a_clean_error(self):
        with self.assertRaises(CommandError):
            call_command("evaluate", "--csv", "does-not-exist.csv", stdout=io.StringIO())
