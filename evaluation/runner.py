"""Runs Maapdand on each test case and compares its verdicts with the expected ones.

Uses the same extractors and rule functions as the web app, but writes nothing to the
database, so an evaluation run never shows up in scan history.
"""
import time
from dataclasses import dataclass, field

from extraction.ocr_extractor import OCRExtractor
from extraction.text_extractor import TextExtractor
from rules.engine import overall_verdict, run_rule
from rules.verdicts import Verdict

PASS, FAIL, CANNOT = Verdict.PASS, Verdict.FAIL, Verdict.CANNOT_DETERMINE


def extract(case):
    """Text cases go through the text parser; image cases through preprocessing + OCR."""
    if case.kind == "text":
        text = "\n".join(p.read_text(encoding="utf-8") for p in case.inputs)
        result = TextExtractor().extract(text)
    else:
        result = OCRExtractor().extract([str(p) for p in case.inputs])
    result.is_imported = case.is_imported  # what the officer would answer on the upload page
    return result


@dataclass
class CaseRun:
    case: object
    got: dict            # rule code -> verdict Maapdand gave
    messages: dict       # rule code -> Maapdand's reason
    seconds: float
    expected_overall: str | None
    got_overall: str


def run_case(case, rules):
    """`rules` are the enabled Rule rows. Returns a CaseRun."""
    start = time.perf_counter()
    result = extract(case)
    got, messages = {}, {}
    for rule in rules:
        outcome = run_rule(rule.code, result)
        got[rule.code], messages[rule.code] = outcome.verdict, outcome.message
    counted = [r.code for r in rules if not r.needs_pack]  # same scope as the web app
    expected_overall = (overall_verdict(case.expected[c] for c in counted)
                        if all(c in case.expected for c in counted) else None)
    return CaseRun(case, got, messages, time.perf_counter() - start,
                   expected_overall, overall_verdict(got[c] for c in counted))


@dataclass
class Score:
    """Counts for one rule (or for the overall verdict) across many cases."""
    scored: int = 0
    correct: int = 0
    missed: int = 0       # expected FAIL, got PASS: a violation waved through (the worst error)
    false_alarm: int = 0  # expected PASS, got FAIL
    deferred: int = 0     # expected a firm verdict, got CANNOT_DETERMINE (a person decides)
    overreach: int = 0    # expected CANNOT_DETERMINE, got a firm verdict
    errors: list = field(default_factory=list)  # (case id, expected, got)

    def add(self, case_id, expected, got):
        self.scored += 1
        if expected == got:
            self.correct += 1
            return
        self.errors.append((case_id, expected, got))
        if expected == FAIL and got == PASS:
            self.missed += 1
        elif expected == PASS and got == FAIL:
            self.false_alarm += 1
        elif got == CANNOT:
            self.deferred += 1
        else:
            self.overreach += 1

    @property
    def accuracy(self):
        return self.correct / self.scored if self.scored else None


def score(runs, codes):
    """Per-rule Scores plus one for the overall verdict."""
    per_rule = {code: Score() for code in codes}
    overall = Score()
    for run in runs:
        for code in codes:
            if code in run.case.expected:
                per_rule[code].add(run.case.id, run.case.expected[code], run.got[code])
        if run.expected_overall:
            overall.add(run.case.id, run.expected_overall, run.got_overall)
    return per_rule, overall
