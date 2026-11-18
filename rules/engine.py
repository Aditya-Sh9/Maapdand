"""Runs the enabled rules against an ExtractionResult and saves the verdicts."""
from . import checks  # noqa: F401  (importing registers every rule function)
from .models import Rule, RuleResult
from .registry import RULE_FUNCTIONS
from .verdicts import RuleOutcome, Verdict


def overall_verdict(verdicts):
    """Any fail -> FAIL. Otherwise any doubt -> CANNOT_DETERMINE. Else PASS.
    Biased toward flagging: a missed violation is worse than an extra flag."""
    verdicts = list(verdicts)
    if Verdict.FAIL in verdicts:
        return Verdict.FAIL
    if Verdict.CANNOT_DETERMINE in verdicts or not verdicts:
        return Verdict.CANNOT_DETERMINE
    return Verdict.PASS


def run_rule(code, result):
    func = RULE_FUNCTIONS.get(code)
    if func is None:  # a Rule row exists in admin but nobody wrote its function yet
        return RuleOutcome(Verdict.CANNOT_DETERMINE, "This rule is not implemented yet.")
    return func(result)


def run_scan(scan, result):
    """Run every enabled Rule, store a RuleResult for each, and set the scan's overall verdict."""
    verdicts = []
    for rule in Rule.objects.filter(enabled=True):
        outcome = run_rule(rule.code, result)
        RuleResult.objects.create(
            scan=scan, rule=rule, verdict=outcome.verdict,
            message=outcome.message, evidence=outcome.evidence,
        )
        if not rule.needs_pack:  # pack checks are reported, not counted (see Rule.needs_pack)
            verdicts.append(outcome.verdict)
    scan.overall_verdict = overall_verdict(verdicts)
    scan.save(update_fields=["overall_verdict"])
    return scan
