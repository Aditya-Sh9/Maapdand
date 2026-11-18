from django.shortcuts import render

from rules.models import Rule


def rule_order(rule):
    """R01-R10 (text checks) first, then M01-M02 (need the physical pack)."""
    return (rule.code.startswith("M"), rule.code)


def landing(request):
    """The home page: what Maapdand does, how it works, what it cannot do."""
    rules = sorted(Rule.objects.filter(enabled=True), key=rule_order)
    return render(request, "core/landing.html", {"rules": rules})
