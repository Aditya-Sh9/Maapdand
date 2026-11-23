"""Small template helpers shared by every page.

A *template tag library* is a Python module in an app's `templatetags/` folder.
Templates load it with `{% load ui %}` and can then call `{% icon "check" %}` etc.
"""
import os
import re
from functools import lru_cache
from pathlib import Path

from django import template
from django.contrib.staticfiles import finders
from django.templatetags.static import static
from django.utils.html import format_html
from django.utils.safestring import mark_safe

from rules.verdicts import Verdict

register = template.Library()

ICON_DIR = Path(__file__).resolve().parent.parent / "icons"

# One icon per verdict, so a verdict is never shown by colour alone (DESIGN.md principle 1).
VERDICT_ICONS = {
    Verdict.PASS: "circle-check",
    Verdict.FAIL: "circle-x",
    Verdict.CANNOT_DETERMINE: "circle-help",
}
VERDICT_CSS = {
    Verdict.PASS: "pass",
    Verdict.FAIL: "fail",
    Verdict.CANNOT_DETERMINE: "cannot",
}


@lru_cache(maxsize=None)
def _icon_body(name):
    """The shapes inside a Lucide SVG file (we draw our own <svg> wrapper around them)."""
    text = (ICON_DIR / f"{name}.svg").read_text(encoding="utf-8")
    return re.search(r"<svg[^>]*>(.*)</svg>", text, re.S).group(1).strip()


@register.simple_tag
def icon(name, size=20, label=""):
    """Inline a Lucide icon. Decorative by default; pass label="..." when the icon alone carries meaning."""
    a11y = format_html('role="img" aria-label="{}"', label) if label else mark_safe('aria-hidden="true"')
    return format_html(
        '<svg class="icon" width="{0}" height="{0}" viewBox="0 0 24 24" fill="none" stroke="currentColor" '
        'stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round" focusable="false" {1}>{2}</svg>',
        size, a11y, mark_safe(_icon_body(name)),
    )


@register.simple_tag
def static_v(path):
    """Like {% static %}, plus "?v=<last-modified time>" so browsers fetch a file again after it changes.

    Without this the browser may keep using its cached copy of maapdand.css after we edit it,
    and a new page shows up unstyled until a hard refresh.
    """
    url = static(path)
    found = finders.find(path)  # the file on disk, looked up the same way runserver serves it
    if not found:
        return url
    return f"{url}?v={int(os.path.getmtime(found))}"


@register.filter
def pct(fraction):
    """0.125 -> "12.50%". Used to place evidence boxes (stored as fractions of the image)."""
    try:
        return f"{float(fraction) * 100:.2f}%"
    except (TypeError, ValueError):
        return "0%"


@register.filter
def verdict_css(verdict):
    return VERDICT_CSS.get(verdict, "cannot")


@register.inclusion_tag("ui/evidence_boxes.html")
def evidence_box(bbox, css="", field="", label="", tag=""):
    """One rectangle drawn over a label image. `bbox` is [left, top, width, height] as fractions."""
    return {"bbox": bbox, "css": css, "field": field, "label": label, "tag": tag}


@register.inclusion_tag("ui/verdict_chip.html")
def verdict_chip(verdict, label=None):
    """Pastel chip with icon + text for Pass / Fail / Cannot determine."""
    return {
        "css": VERDICT_CSS.get(verdict, "cannot"),
        "icon_name": VERDICT_ICONS.get(verdict, "circle-help"),
        "text": label or Verdict(verdict).label,
    }


@register.inclusion_tag("ui/stepper.html")
def stepper(current):
    """The four-step progress bar (Upload, Read, Review, Result). `current` is 1-4."""
    names = ["Upload", "Read", "Review", "Result"]
    steps = []
    for number, name in enumerate(names, start=1):
        state = "done" if number < current else "current" if number == current else "todo"
        steps.append({"number": number, "name": name, "state": state})
    return {"steps": steps, "current": current}
