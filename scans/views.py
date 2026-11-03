from django.shortcuts import get_object_or_404, redirect, render

from .models import Scan
from .services import run_text_scan


def check_text(request):
    """GET shows the empty form. POST runs the checks and redirects to the result."""
    if request.method == "POST":
        text = request.POST.get("label_text", "").strip()
        if text:
            scan = run_text_scan(text, user=request.user)
            return redirect("scan_result", pk=scan.pk)
    return render(request, "scans/check_text.html")


def scan_result(request, pk):
    scan = get_object_or_404(Scan, pk=pk)
    return render(request, "scans/result.html", {"scan": scan, "results": scan.results.select_related("rule")})
