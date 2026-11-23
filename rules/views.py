from django.http import FileResponse, Http404
from django.shortcuts import render

from core.views import rule_order

from . import documents
from .models import Rule


def rule_list(request):
    """Read-only list of every rule with its legal clause (the rule browser)."""
    rules = sorted(Rule.objects.all(), key=rule_order)
    return render(request, "rules/rule_list.html", {"rules": rules})


def document_list(request):
    """The Documents tab: official gazette PDFs the rules are based on."""
    return render(request, "rules/document_list.html", {
        "documents": documents.documents_with_status(),
        "source_url": documents.SOURCE_URL,
    })


def document_file(request, slug):
    """Send one PDF. ?download=1 saves it; otherwise the browser shows it in the tab."""
    doc = documents.get_document(slug)
    path = documents.REFERENCE_DIR / doc["filename"] if doc else None
    if path is None or not path.is_file():
        raise Http404("Document not found")
    return FileResponse(
        open(path, "rb"),
        content_type="application/pdf",
        as_attachment=request.GET.get("download") == "1",
        filename=doc["filename"],
    )
