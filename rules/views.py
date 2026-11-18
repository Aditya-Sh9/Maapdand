from django.shortcuts import render

from core.views import rule_order

from .models import Rule


def rule_list(request):
    """Read-only list of every rule with its legal clause (the rule browser)."""
    rules = sorted(Rule.objects.all(), key=rule_order)
    return render(request, "rules/rule_list.html", {"rules": rules})
