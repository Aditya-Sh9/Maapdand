"""`python manage.py evaluate`: measure how often Maapdand gives the right verdict.

A *management command* is a Python class Django runs from the command line, like
`migrate` or `runserver`. Django finds it because the file sits in
<app>/management/commands/<name>.py and defines a class called Command.
"""
from datetime import date
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError

from core.views import rule_order
from evaluation.dataset import DATA_DIR, DatasetError, load_cases
from evaluation.runner import run_case, score
from rules.models import Rule

RESULTS_DIR = Path(__file__).resolve().parents[2] / "results"


def pct(score):
    return "n/a" if score.accuracy is None else f"{score.accuracy:.0%}"


class Command(BaseCommand):
    help = "Run every labelled test case and report per-rule accuracy and missed violations."

    def add_arguments(self, parser):
        parser.add_argument("--csv", default=str(DATA_DIR / "cases.csv"), help="Path to the cases CSV.")
        parser.add_argument("--only", choices=["text", "image"], help="Run only text or only image cases.")
        parser.add_argument("--real-only", action="store_true", help="Skip synthetic (made-up) cases.")
        parser.add_argument("--errors", action="store_true", help="List every wrong verdict with Maapdand's reason.")
        parser.add_argument("--save", action="store_true", help="Also write a Markdown report to evaluation/results/.")

    def handle(self, *args, **options):
        try:
            cases = load_cases(options["csv"])
        except DatasetError as error:
            raise CommandError(str(error))
        if options["only"]:
            cases = [c for c in cases if c.kind == options["only"]]
        if options["real_only"]:
            cases = [c for c in cases if not c.synthetic]
        if not cases:
            raise CommandError("No cases to run with these options.")

        rules = sorted(Rule.objects.filter(enabled=True), key=rule_order)
        codes = [r.code for r in rules]
        runs = []
        for case in cases:
            self.stdout.write(f"  {case.id} ({case.kind})...", ending="")
            runs.append(run_case(case, rules))
            self.stdout.write(f" {runs[-1].seconds:.1f}s")

        # Real and synthetic cases are reported apart, so made-up labels never pass for field accuracy.
        groups = [("All cases", runs)]
        real = [r for r in runs if not r.case.synthetic]
        synthetic = [r for r in runs if r.case.synthetic]
        if real and synthetic:
            groups += [("Real labels only", real), ("Synthetic labels only", synthetic)]

        lines = [f"# Maapdand evaluation, {date.today():%d %b %Y}", "",
                 f"Cases: {len(runs)} ({len(real)} real, {len(synthetic)} synthetic). "
                 f"Text: {sum(r.case.kind == 'text' for r in runs)}, images: {sum(r.case.kind == 'image' for r in runs)}.", ""]
        for title, group in groups:
            per_rule, overall = score(group, codes)
            lines += [f"## {title} ({len(group)})", "",
                      "| Rule | Scored | Correct | Accuracy | Missed violations | False alarms | Sent to a person | Overreach |",
                      "|---|---|---|---|---|---|---|---|"]
            for rule in rules:
                s = per_rule[rule.code]
                lines.append(f"| {rule.code} {rule.title} | {s.scored} | {s.correct} | {pct(s)} | {s.missed} | "
                             f"{s.false_alarm} | {s.deferred} | {s.overreach} |")
            lines.append(f"| **Overall verdict** | {overall.scored} | {overall.correct} | **{pct(overall)}** | "
                         f"{overall.missed} | {overall.false_alarm} | {overall.deferred} | {overall.overreach} |")
            missed = sum(s.missed for s in per_rule.values())
            lines += ["", f"Missed violations (expected Fail, got Pass): **{missed}**.", ""]

        if options["errors"]:
            lines += ["## Wrong verdicts", ""]
            for run in runs:
                for code in codes:
                    want = run.case.expected.get(code)
                    if want and want != run.got[code]:
                        lines.append(f"- {run.case.id} {code}: expected {want}, got {run.got[code]}. "
                                     f"Maapdand said: {run.messages[code]}")
            lines.append("")

        lines += ["Columns: *Missed violations* = a Fail reported as Pass (the error a screening aid must avoid). "
                  "*Sent to a person* = Cannot determine where a firm verdict was expected. "
                  "*Overreach* = a firm verdict where Cannot determine was expected.", ""]
        report = "\n".join(lines)
        self.stdout.write("")
        self.stdout.write(report)

        if options["save"]:
            RESULTS_DIR.mkdir(exist_ok=True)
            path = RESULTS_DIR / f"{date.today():%Y-%m-%d}.md"
            path.write_text(report, encoding="utf-8")
            self.stdout.write(self.style.SUCCESS(f"Saved {path}"))
