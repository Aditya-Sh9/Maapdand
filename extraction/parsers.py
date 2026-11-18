"""Small functions that find one field in label text. Each returns the matched text
or None. Keywords (English + Hindi) live in keywords.py; this file only builds patterns."""
import re
from decimal import Decimal

from .keywords import (
    BEST_BEFORE, CONSUMER_CARE, COUNTRY_OF_ORIGIN, CURRENCY, DATE_WORDS, DURATION_UNITS,
    GENERIC_NAME, IMPORTED, MAKER_HINDI, MAKER_VERBS, MFG_DATE, MONTHS, MRP, NET_QUANTITY,
    PACKED_DATE, PER, QUANTITY_QUALIFIERS, TAX_NOTE, UNIT_SALE_PRICE, UNITS, any_of,
)

# Label text may use Devanagari digits; turn them into 0-9 before any matching.
_DEVANAGARI_DIGITS = str.maketrans("०१२३४५६७८९", "0123456789")

_FLAGS = re.IGNORECASE | re.DOTALL

# Shared pieces. "Not followed by a letter" instead of \b, because \b misbehaves
# after Hindi vowel signs (e.g. the final "ा" in "किग्रा").
_NO_LETTER_AFTER = r"(?![^\W\d_])"
_NUMBER = r"\d[\d,]*(?:\.\d+)?"
_UNIT = any_of(UNITS) + _NO_LETTER_AFTER
_DATE = (
    r"(?:(?:\d{1,2}\s*[/\-.]\s*)?\d{1,2}\s*[/\-.]\s*(?:\d{4}|\d{2})\b"  # 05/2025, 12/05/2025
    r"|" + any_of(MONTHS) + r"[a-z]*\.?[\s,.\-/]*(?:\d{4}|\d{2})\b)"  # May 2025, MAY-25
)
_SEP = r"[\s:.\-]*"  # spaces / colon / dot / dash between a keyword and its value
_LINE_VALUE = r"[^\W\d_][^\n,;|]{1,59}"  # a short value that starts with a letter, up to end of line

_MANUFACTURER = re.compile(
    r"(?:" + any_of(MAKER_VERBS)
    + r"(?:\s*(?:and|&)\s*" + any_of(MAKER_VERBS) + r")?\s+by"
    + r"|" + any_of(MAKER_HINDI) + r")"
    + r"[\s:\-]*.{0,200}",  # keyword plus the next ~200 chars, which should hold name + address
    _FLAGS,
)

_IMPORTED = re.compile(any_of(IMPORTED), _FLAGS)

_GENERIC_NAME = re.compile(any_of(GENERIC_NAME) + _SEP + _LINE_VALUE, _FLAGS)

_NET_QUANTITY = re.compile(
    # An optional "approx." / "min." may sit before the number: the quantity is still declared
    # (R03 passes) and R04 separately fails the qualifier.
    any_of(NET_QUANTITY) + r"\.?\s*[:\-]?\s*(?:" + any_of(QUANTITY_QUALIFIERS) + r"\s*)?" + _NUMBER + r"\s*" + _UNIT,
    _FLAGS,
)
_AMOUNT_AND_UNIT = re.compile(r"(" + _NUMBER + r")\s*(" + _UNIT + r")", _FLAGS)

# "Net Wt. approx. 250 g": a forbidden qualifier within a few characters of the keyword.
_QUANTITY_QUALIFIER = re.compile(
    any_of(NET_QUANTITY) + r"[^\n\d]{0,25}?" + any_of(QUANTITY_QUALIFIERS) + _NO_LETTER_AFTER, _FLAGS
)


def _date_pattern(keywords):
    """Keyword (optionally "Mfg./Pkd.") + optional "date"/"on" + a date."""
    either = any_of(MFG_DATE + PACKED_DATE)
    return re.compile(
        any_of(keywords) + r"(?:\s*[/&]\s*" + either + r")?"
        + r"(?:\s*" + any_of(DATE_WORDS) + r")*\s*[:\-.]?\s*" + _DATE,
        _FLAGS,
    )


_MFG_DATE = _date_pattern(MFG_DATE)
_PACKED_DATE = _date_pattern(PACKED_DATE)

_BEST_BEFORE = re.compile(
    any_of(BEST_BEFORE) + _SEP
    + r"(?:" + _DATE
    + r"|\d+\s*" + any_of(DURATION_UNITS) + _NO_LETTER_AFTER  # "6 months"
    + r"(?:\s*from\s*(?:the\s*)?(?:date\s*of\s*)?(?:mfg|mfd|manufacture|manufacturing|packing|packed|pkd)\.?)?)",
    _FLAGS,
)

_MRP = re.compile(
    any_of(MRP)
    + r"[\s:.\-]*(?:\([^)]*\)[\s:.\-]*)?"  # optional "(Incl. of all taxes)" between keyword and price
    + any_of(CURRENCY) + r"?\s*\d[\d,]*(?:\.\d+)?",
    _FLAGS,
)

_TAX_NOTE = re.compile(any_of(TAX_NOTE), _FLAGS)

# Either "Unit sale price: ₹0.48/g" or a bare "₹ 48 per 100 g". The bare form needs a
# currency sign so a plain "250/g" is not mistaken for a price.
_UNIT_SALE_PRICE = re.compile(
    r"(?:" + any_of(UNIT_SALE_PRICE) + _SEP + any_of(CURRENCY) + r"?|" + any_of(CURRENCY) + r")"
    + r"\s*" + _NUMBER + r"\s*" + any_of(PER) + r"\s*(?:" + _NUMBER + r"\s*)?" + _UNIT,
    _FLAGS,
)

_PRICE_PER_UNIT = re.compile(
    r"(" + _NUMBER + r")\s*" + any_of(PER) + r"\s*(?:(" + _NUMBER + r")\s*)?(" + _UNIT + r")", _FLAGS
)

_CONSUMER_CARE = re.compile(any_of(CONSUMER_CARE) + r"[\s:\-]*.{0,200}", _FLAGS)

_EMAIL = re.compile(r"[\w.+\-]+@[\w\-]+(?:\.[\w\-]+)+")

# Indian phone formats. The (?<!\d)/(?!\d) guards stop a 13-digit barcode or a
# 6-digit PIN code from being read as a phone number.
_PHONE = re.compile(
    r"(?<!\d)(?:"
    r"(?:\+91[\s\-]?|0)?[6-9]\d{4}[\s\-]?\d{5}"  # mobile: 98765 43210, +91-9876543210
    r"|1800[\s\-]?\d{3}[\s\-]?\d{3,4}"  # toll free: 1800-123-4567
    r"|0\d{2,4}[\s\-]\d{6,8}"  # landline with STD code: 022-12345678
    r")(?!\d)"
)

_COUNTRY_OF_ORIGIN = re.compile(any_of(COUNTRY_OF_ORIGIN) + _SEP + _LINE_VALUE, _FLAGS)

_PIN_CODE = re.compile(r"\b\d{6}\b")


def normalize_text(text):
    return text.translate(_DEVANAGARI_DIGITS)


def _first(pattern, text):
    match = pattern.search(text)
    return " ".join(match.group(0).split()) if match else None  # collapse whitespace


# A line that starts a new labelled field ("MRP: 45", "Net Quantity - 500 g").
_NEW_LABEL_LINE = re.compile(r"^\s*[^\W\d_][\w .()/]{0,30}\s*[:\-]\s*\S")
_MAX_MAKER_LINES = 3  # name + address rarely needs more than three lines


def find_manufacturer(text):
    """The maker keyword plus its name and address. The pattern grabs ~200 characters
    so a multi-line address is not cut off; here we cut it back at the next labelled
    line so other fields (MRP, quantity...) do not end up inside the manufacturer."""
    match = _MANUFACTURER.search(text)
    if not match:
        return None
    lines = match.group(0).split("\n")
    kept = [lines[0]]
    for line in lines[1:_MAX_MAKER_LINES]:
        if not line.strip() or _NEW_LABEL_LINE.match(line):
            break
        kept.append(line)
    return " ".join(" ".join(kept).split())


def find_import_statement(text):
    """'Imported by' / 'आयातक': a signal that country of origin is required."""
    return _first(_IMPORTED, text)


def find_generic_name(text):
    """Only finds an explicitly labelled name ('Product name: ...'). Labels that just
    print the name as a heading are not caught; the reviewer adds those by hand."""
    return _first(_GENERIC_NAME, text)


def find_net_quantity(text):
    return _first(_NET_QUANTITY, text)


def split_quantity(text):
    """'Net Wt. 1,000 g' -> (Decimal('1000'), 'g'). Returns None if no number + unit."""
    match = _AMOUNT_AND_UNIT.search(text)
    if not match:
        return None
    return Decimal(match.group(1).replace(",", "")), match.group(2).lower()


def find_quantity_qualifier(text):
    return _first(_QUANTITY_QUALIFIER, text)


def find_mfg_date(text):
    return _first(_MFG_DATE, text)


def find_packed_date(text):
    return _first(_PACKED_DATE, text)


def find_best_before(text):
    return _first(_BEST_BEFORE, text)


def find_mrp(text):
    return _first(_MRP, text)


def find_mrp_tax_note(text):
    return _first(_TAX_NOTE, text)


def find_unit_sale_price(text):
    return _first(_UNIT_SALE_PRICE, text)


def split_unit_sale_price(text):
    """'₹ 48 per 100 g' -> (Decimal('48'), Decimal('100'), 'g'). Per-amount defaults to 1."""
    match = _PRICE_PER_UNIT.search(text)
    if not match:
        return None
    price, per_amount, unit = match.groups()
    per_amount = Decimal(per_amount.replace(",", "")) if per_amount else Decimal(1)
    return Decimal(price.replace(",", "")), per_amount, unit.lower()


def find_consumer_care(text):
    return _first(_CONSUMER_CARE, text)


def find_email(text):
    return _first(_EMAIL, text)


def find_phone(text):
    return _first(_PHONE, text)


def find_country_of_origin(text):
    return _first(_COUNTRY_OF_ORIGIN, text)


def has_pin_code(text):
    return bool(_PIN_CODE.search(text))
