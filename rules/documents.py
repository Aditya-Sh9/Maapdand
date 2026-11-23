"""The official documents shown in the Documents tab.

The PDFs live in docs/reference/. This list is also an allowlist: the view only
serves a file whose name is listed here, so nobody can ask for some other file
on the disk by editing the URL.
"""
from pathlib import Path

from django.conf import settings

REFERENCE_DIR = Path(settings.BASE_DIR) / "docs" / "reference"

SOURCE_URL = "https://consumeraffairs.gov.in/pages/legal-metrology-act"

# Oldest first, so it reads as the principal rules followed by their amendments.
DOCUMENTS = [
    {
        "slug": "principal-rules-2011",
        "filename": "2011-03-07 GSR 202(E) Principal Rules 2011 (state copy).pdf",
        "title": "Principal Rules, 2011",
        "notification": "GSR 202(E)",
        "date": "7 Mar 2011",
        "kind": "Principal rules",
        "summary": "The original Legal Metrology (Packaged Commodities) Rules. Copy from the Nagaland Legal Metrology site; includes GSR 748(E) Oct 2011 notes.",
    },
    {
        "slug": "amendment-2017",
        "filename": "2017-06-23 GSR 629(E) Amendment Rules 2017.pdf",
        "title": "Amendment Rules, 2017",
        "notification": "GSR 629(E)",
        "date": "23 Jun 2017",
        "kind": "Amendment",
        "summary": "From 1 Jan 2018: country of origin 6(1)(aa); best before / use by 6(1)(da); MRP “inclusive of all taxes” wording; Rule 7 Table I by panel area.",
    },
    {
        "slug": "amendment-2021",
        "filename": "2021-11-02 GSR 779(E) Amendment Rules 2021.pdf",
        "title": "Amendment Rules, 2021",
        "notification": "GSR 779(E)",
        "date": "2 Nov 2021",
        "kind": "Amendment",
        "summary": "From 1 Apr 2022: month and year of manufacture only in 6(1)(d); number / unit / piece / pair / set allowed in 13(5)(ii); first 6(11) unit sale price.",
    },
    {
        "slug": "amendment-2022",
        "filename": "2022-03-28 GSR 226(E) Amendment Rules 2022 (unit sale price).pdf",
        "title": "Amendment Rules, 2022 (unit sale price)",
        "notification": "GSR 226(E)",
        "date": "28 Mar 2022",
        "kind": "Amendment",
        "summary": "Substitutes 6(11): unit sale price per g / kg, ml / L, cm / m, or number. Start date postponed by later notices.",
    },
    {
        "slug": "amendment-2023",
        "filename": "2023-10-06 GSR 722(E) Amendment Rules 2023.pdf",
        "title": "Amendment Rules, 2023",
        "notification": "GSR 722(E)",
        "date": "6 Oct 2023",
        "kind": "Amendment",
        "summary": "From 1 Jan 2024: unit sale price not needed for combination, group or multi-piece packs; manufacture-date rules for spare parts.",
    },
    {
        "slug": "fourth-amendment-2026",
        "filename": "2026-09-21 GSR 826(E) Fourth Amendment Rules 2026 (veg dot).pdf",
        "title": "Fourth Amendment Rules, 2026 (veg dot)",
        "notification": "GSR 826(E)",
        "date": "21 Sep 2026",
        "kind": "Amendment",
        "summary": "6(4A)(d): green / red-brown dot on soap, shampoo, toothpaste and cosmetics. 6(8) omitted.",
    },
]


def get_document(slug):
    """Return the document with this slug, or None."""
    for doc in DOCUMENTS:
        if doc["slug"] == slug:
            return doc
    return None


def documents_with_status():
    """Each document plus whether its PDF is on disk and its size in MB."""
    rows = []
    for doc in DOCUMENTS:
        path = REFERENCE_DIR / doc["filename"]
        exists = path.is_file()
        rows.append({
            **doc,
            "available": exists,
            "size_mb": round(path.stat().st_size / 1_048_576, 1) if exists else None,
        })
    return rows
