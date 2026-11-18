from django.db import models

from .verdicts import Verdict


class Rule(models.Model):
    """Metadata about one rule. The logic lives in rules/checks.py; this row lets
    us switch a rule on/off or change its severity from Django admin."""

    class Severity(models.TextChoices):
        CRITICAL = "critical", "Critical"
        MAJOR = "major", "Major"
        MINOR = "minor", "Minor"

    code = models.CharField(max_length=10, unique=True)  # e.g. "R06", matches the registry
    title = models.CharField(max_length=200)
    description = models.TextField(help_text="Plain-English explanation of what is checked.")
    legal_reference = models.CharField(max_length=200, blank=True)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.MAJOR)
    enabled = models.BooleanField(default=True)
    required_fields = models.JSONField(default=list, blank=True)
    # True for checks that need the physical pack (letter height, display panel). They are
    # shown on the result page but left out of the overall verdict, which text can settle.
    needs_pack = models.BooleanField(default=False)

    class Meta:
        ordering = ["code"]

    def __str__(self):
        return f"{self.code}: {self.title}"


class RuleResult(models.Model):
    """The outcome of one rule for one scan."""

    scan = models.ForeignKey("scans.Scan", on_delete=models.CASCADE, related_name="results")
    rule = models.ForeignKey(Rule, on_delete=models.PROTECT)
    verdict = models.CharField(max_length=20, choices=Verdict.choices)
    message = models.TextField(blank=True)
    evidence = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["rule__code"]

    def __str__(self):
        return f"{self.scan_id} {self.rule.code} {self.verdict}"
