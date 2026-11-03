"""Small functions that find one field in label text. Each returns the matched text
or None. English and Hindi keywords are both supported."""
import re

# Label text may use Devanagari digits; turn them into 0-9 before any matching.
_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

_FLAGS = re.IGNORECASE | re.DOTALL

_MANUFACTURER = re.compile(
    r"(?:(?:manufactured|marketed|packed|packaged|imported|mfd\.?|mfg\.?)"
    r"(?:\s*(?:and|&)\s*(?:manufactured|marketed|packed|packaged|imported))?\s+by"
    r"|निर्माता|पैकर|आयातक|विपणनकर्ता)"
    r"[\s:\-]*.{0,200}",  # keyword plus the next ~200 chars, which should hold name + address
    _FLAGS,
)

_NET_QUANTITY = re.compile(
    r"(?:net\s*(?:qty|quantity|wt|weight|content|contents|vol|volume)|शुद्ध\s*मात्रा|निवल\s*मात्रा)"
    r"\.?\s*[:\-]?\s*"
    r"\d+(?:\.\d+)?\s*"
    r"(?:kg|gms|gm|mg|g|ml|litres|litre|liter|ltr|l|nos|no|pcs|pc|pieces|units|unit|cm|m)\b",
    _FLAGS,
)

_MONTHS = r"(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\.?"
_MFG_DATE = re.compile(
    r"(?:mfg\.?|mfd\.?|manufactured|manufacturing|packed|packing|pkd\.?|निर्माण)"
    r"(?:\s*(?:date|on|तिथि|दिनांक|माह))*\s*[:\-.]?\s*"
    r"(?:(?:\d{1,2}\s*[/\-.]\s*)?\d{1,2}\s*[/\-.]\s*(?:\d{4}|\d{2})\b"  # 05/2025, 12/05/2025
    r"|" + _MONTHS + r"[\s,.\-/]*(?:\d{4}|\d{2})\b)",  # May 2025, MAY-25
    _FLAGS,
)

_MRP = re.compile(
    r"(?:m\.?\s*r\.?\s*p\.?|max(?:imum)?\.?\s*retail\s*price|अधिकतम\s*खुदरा\s*मूल्य)"
    r"[\s:.\-]*(?:\([^)]*\)[\s:.\-]*)?"  # optional "(Incl. of all taxes)" between keyword and price
    r"(?:(?:rs|inr)\.?|₹|रु\.?)?\s*\d[\d,]*(?:\.\d+)?",
    _FLAGS,
)

_TAX_NOTE = re.compile(
    r"incl(?:usive|\.)?\s*of\s*all\s*taxes|सभी\s*करों\s*(?:सहित|समेत)", _FLAGS
)

_PIN_CODE = re.compile(r"\b\d{6}\b")


def normalize_text(text):
    return text.translate(_DEVANAGARI_DIGITS)


def _first(pattern, text):
    match = pattern.search(text)
    return " ".join(match.group(0).split()) if match else None  # collapse whitespace


def find_manufacturer(text):
    return _first(_MANUFACTURER, text)


def find_net_quantity(text):
    return _first(_NET_QUANTITY, text)


def find_mfg_date(text):
    return _first(_MFG_DATE, text)


def find_mrp(text):
    return _first(_MRP, text)


def find_mrp_tax_note(text):
    return _first(_TAX_NOTE, text)


def has_pin_code(text):
    return bool(_PIN_CODE.search(text))
