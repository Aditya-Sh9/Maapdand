"""The three possible answers for a rule, and the object a rule function returns."""
from dataclasses import dataclass, field

from django.db import models


class Verdict(models.TextChoices):
    # Three states, never two: if we can't tell, we say so instead of guessing a pass.
    PASS = "PASS", "Pass"
    FAIL = "FAIL", "Fail"
    CANNOT_DETERMINE = "CANNOT_DETERMINE", "Cannot determine"


@dataclass
class RuleOutcome:
    """What one rule function returns: a verdict, a plain-English reason, and proof."""
    verdict: str
    message: str
    evidence: dict = field(default_factory=dict)
