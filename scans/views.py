from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render

from core.views import rule_order
from rules.verdicts import Verdict

from .forms import UploadForm
from .models import Scan

from .services import (
    apply_review_and_run, check_image_quality, create_image_scan,
    result_rows, review_rows, run_text_scan, verdict_summary,
)

MAX_IMAGE_MB = 10
MAX_IMAGES = 6


def check_text(request):
    """GET shows the empty form. POST runs the checks and redirects to the result."""
    if request.method == "POST":
        text = request.POST.get("label_text", "").strip()
        is_imported = {"yes": True, "no": False}.get(request.POST.get("is_imported"))
        if text:
            scan = run_text_scan(text, user=request.user, is_imported=is_imported)
            return redirect("scan_result", pk=scan.pk)
    return render(request, "scans/check_text.html")


def upload_images(request):
    """GET shows the upload form. POST checks the images, reads them with OCR,
    then sends the person to the review page (no verdict yet)."""
    # Not `request.POST or None`: a POST holding only files has an empty request.POST.
    form = UploadForm(request.POST if request.method == "POST" else None)
    problems = []
    if request.method == "POST" and form.is_valid():
        files = request.FILES.getlist("images")
        if not files:
            problems.append("Choose at least one image.")
        elif len(files) > MAX_IMAGES:
            problems.append(f"Upload at most {MAX_IMAGES} images per product.")
        else:
            for f in files:
                if f.size > MAX_IMAGE_MB * 1024 * 1024:
                    problems.append(f"{f.name}: larger than {MAX_IMAGE_MB} MB.")
                    continue
                _, ok, reasons = check_image_quality(f)  # the quality gate
                if not ok and not form.cleaned_data["use_anyway"]:
                    problems.append(f"{f.name}: {' '.join(reasons)}")
        if not problems:
            scan = create_image_scan(
                files,
                category=form.cleaned_data["category"],
                name=form.cleaned_data["name"],
                is_imported=form.imported_value(),
                user=request.user,
            )
            return redirect("scan_review", pk=scan.pk)
    return render(request, "scans/upload.html", {"form": form, "problems": problems})


def scan_review(request, pk):
    """Show what OCR read, let the person fix it, then run the rules on the final values."""
    scan = get_object_or_404(Scan, pk=pk)
    if request.method == "POST":
        corrections = {
            key.removeprefix("field_"): value
            for key, value in request.POST.items() if key.startswith("field_")
        }
        apply_review_and_run(scan, corrections)
        return redirect("scan_result", pk=scan.pk)
    images = scan.product.images.all() if scan.product else []
    found, missing = review_rows(scan)
    return render(request, "scans/review.html", {
        "scan": scan, "found": found, "missing": missing, "images": images,
        "total_fields": len(found) + len(missing),
    })


def result_context(scan):
    """Everything the result page and the printable report both show."""
    rows = result_rows(scan, rule_order)
    # Label checks decide the overall verdict; pack checks (M01, M02) are shown on their own.
    label_rows = [r for r in rows if not r["rule"].needs_pack]
    pack_rows = [r for r in rows if r["rule"].needs_pack]
    return {
        "scan": scan, "rows": rows, "label_rows": label_rows, "pack_rows": pack_rows,
        "summary": verdict_summary(label_rows),
        "images": scan.product.images.all() if scan.product else [],
        # Failed or doubtful label checks with no box on the image, listed under it so nothing is silent.
        "unlocated": [r for r in label_rows if not r["boxes"] and r["result"].verdict != Verdict.PASS],
    }


def scan_result(request, pk):
    scan = get_object_or_404(Scan, pk=pk)
    if not scan.overall_verdict:  # image scan that has not been reviewed yet
        return redirect("scan_review", pk=scan.pk)
    return render(request, "scans/result.html", result_context(scan))


def scan_report(request, pk):
    """A document version of the result, laid out for A4. The browser's
    "Save as PDF" turns it into the PDF report (it shapes Hindi text correctly)."""
    scan = get_object_or_404(Scan, pk=pk)
    if not scan.overall_verdict:
        return redirect("scan_review", pk=scan.pk)
    context = result_context(scan)
    context["fields"] = review_rows(scan)[0]  # the values the rules ran on, with any corrections
    return render(request, "scans/report.html", context)


HISTORY_FILTERS = [
    ("", "All"),
    (Verdict.FAIL, "Fail"),
    (Verdict.CANNOT_DETERMINE, "Cannot determine"),
    (Verdict.PASS, "Pass"),
    ("pending", "Awaiting review"),
]


def scan_history(request):
    """Every scan, newest first, 20 per page, optionally filtered by overall verdict."""
    label_results = Q(results__rule__needs_pack=False)
    scans = Scan.objects.select_related("product").annotate(
        image_count=Count("product__images", distinct=True),
        failed=Count("results", filter=label_results & Q(results__verdict=Verdict.FAIL), distinct=True),
        doubtful=Count("results", filter=label_results & Q(results__verdict=Verdict.CANNOT_DETERMINE), distinct=True),
    )
    current = request.GET.get("verdict", "")
    if current == "pending":
        scans = scans.filter(overall_verdict="")
    elif current in Verdict.values:
        scans = scans.filter(overall_verdict=current)
    else:
        current = ""
    # Paginator splits a queryset into pages; get_page() copes with a missing or bad ?page= value.
    page = Paginator(scans, 20).get_page(request.GET.get("page"))
    return render(request, "scans/history.html", {
        "page": page, "filters": HISTORY_FILTERS, "current": current,
    })
