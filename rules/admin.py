from django.contrib import admin

from .models import Rule, RuleResult


@admin.register(Rule)
class RuleAdmin(admin.ModelAdmin):
    list_display = ["code", "title", "severity", "enabled"]
    list_editable = ["severity", "enabled"]  # toggle rules straight from the list page


@admin.register(RuleResult)
class RuleResultAdmin(admin.ModelAdmin):
    list_display = ["scan", "rule", "verdict"]
    list_filter = ["verdict"]
