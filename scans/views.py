from django.shortcuts import get_object_or_404, redirect, render

from .forms import UploadForm
from .models import Scan
from .services import (
    apply_review_and_run, check_image_quality, create_image_scan, review_rows, run_text_scan,
)

MAX_IMAGE_MB = 10
MAX_IMAGES = 6


def check_text(request):
    """GET shows the empty form. POST runs the checks and redirects to the result."""
    if request.method == "POST":
        text = request.POST.get("label_text", "").strip()
        if text:
            scan = run_text_scan(text, user=request.user)
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
    return render(request, "scans/review.html", {
        "scan": scan, "rows": review_rows(scan), "images": images,
    })


def scan_result(request, pk):
    scan = get_object_or_404(Scan, pk=pk)
    if not scan.overall_verdict:  # image scan that has not been reviewed yet
        return redirect("scan_review", pk=scan.pk)
    return render(request, "scans/result.html", {"scan": scan, "results": scan.results.select_related("rule")})
