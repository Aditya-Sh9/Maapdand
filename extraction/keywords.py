"""Label keywords in English and Hindi, kept in one place.

Each entry is a small regex fragment (so "net\\s*wt" matches "Net Wt" and "NetWt").
Parsers build their patterns from these lists, so supporting a new spelling or a new
language means adding one string here, not touching the parser code.
"""

# --- Who made / packed / imported it (R01) ---
MAKER_VERBS = ["manufactured", "marketed", "packed", "packaged", "imported", r"mfd\.?", r"mfg\.?"]
MAKER_HINDI = ["निर्माता", "पैकर", "आयातक", "विपणनकर्ता"]

# --- Imported product signal (R08) ---
IMPORTED = [r"imported\s+by", r"importer", "आयातक", "आयातित"]

# --- Generic / common name (R02) ---
GENERIC_NAME = [
    r"generic\s*name", r"common\s*name", r"name\s*of\s*(?:the\s*)?(?:commodity|product)",
    r"product\s*name",
    "उत्पाद\\s*का\\s*नाम", "वस्तु\\s*का\\s*नाम",
]

# --- Net quantity (R03, R04) ---
NET_QUANTITY = [
    r"net\s*(?:qty|quantity|wt|weight|content|contents|vol|volume)",
    "शुद्ध\\s*मात्रा", "निवल\\s*मात्रा", "शुद्ध\\s*वजन",
]
# Units as they appear on labels, longest first so "ml" is tried before "m".
# Whether a unit is a *standard* one is decided by rule R04, not here.
UNITS = [
    "litres", "litre", "liters", "liter", "ltr", "kg", "gms", "gm", "mg", "g", "ml", "l",
    "numbers", "number", "pieces", "piece", "pcs", "pc", "pairs", "pair", "sets", "set",
    "nos", "no", "units", "unit", "n", "u", "cm", "metres", "metre", "meters", "meter", "m",
    "किग्रा", "ग्राम", "मिली", "लीटर", "नग",
]
# Words Rule 12(6) forbids in a quantity declaration ("Net Wt. approx. 250 g").
QUANTITY_QUALIFIERS = [
    "about", r"approx\.?", "approximately", "minimum", r"min\.", r"not\s*less\s*than",
    "average", r"avg\.?", "लगभग", "न्यूनतम", "औसत",
]

# --- Dates (R05, R10) ---
MONTHS = [r"jan", r"feb", r"mar", r"apr", r"may", r"jun", r"jul", r"aug", r"sept?", r"oct", r"nov", r"dec"]
# Since the 2021 amendment, Rule 6(1)(d) asks for the month of *manufacture*; a packing
# date alone is no longer enough, so the two are kept apart.
MFG_DATE = [r"mfg\.?", r"mfd\.?", "manufactured", "manufacturing", r"date\s*of\s*manufacture", "निर्माण"]
PACKED_DATE = ["packed", "packing", r"pkd\.?", r"date\s*of\s*packing", "पैकिंग"]
DATE_WORDS = ["date", "on", "तिथि", "दिनांक", "माह"]
BEST_BEFORE = [
    r"best\s*before", r"use\s*by", r"use\s*before", r"expiry(?:\s*date)?", r"exp\.?(?:\s*date)?",
    "उपयोग\\s*की\\s*अंतिम\\s*तिथि", "समाप्ति\\s*तिथि", "पहले\\s*उपयोग\\s*करें",
]
DURATION_UNITS = [r"months?", r"days?", r"years?", r"weeks?", "माह", "महीने", "दिन", "वर्ष", "सप्ताह"]

# --- Price (R06, R09) ---
MRP = [r"m\.?\s*r\.?\s*p\.?", r"max(?:imum)?\.?\s*retail\s*price", "अधिकतम\\s*खुदरा\\s*मूल्य"]
CURRENCY = [r"rs\.?", r"inr\.?", "₹", r"रु\.?"]
TAX_NOTE = [r"incl(?:usive|\.)?\s*of\s*all\s*taxes", "सभी\\s*करों\\s*(?:सहित|समेत)"]
UNIT_SALE_PRICE = [r"unit\s*sale\s*price", r"\bu\.?s\.?p\b\.?", "इकाई\\s*विक्रय\\s*मूल्य"]
PER = [r"/", r"per", "प्रति"]

# --- Consumer care (R07) ---
CONSUMER_CARE = [
    r"consumer\s*care", r"customer\s*care", r"consumer\s*(?:complaints?|helpline|cell)",
    r"customer\s*(?:support|service|helpline)", r"for\s*(?:any\s*)?(?:complaints?|queries|feedback)",
    r"toll\s*free", r"helpline", r"contact\s*us",
    "उपभोक्ता\\s*सेवा", "ग्राहक\\s*सेवा", "उपभोक्ता\\s*शिकायत", "संपर्क\\s*करें",
]

# --- Country of origin (R08) ---
COUNTRY_OF_ORIGIN = [r"country\s*of\s*origin", r"made\s*in", r"product\s*of", "मूल\\s*देश", "उद्गम\\s*देश"]


def any_of(fragments):
    """Join fragments into one non-capturing regex group: (?:a|b|c)."""
    return "(?:" + "|".join(fragments) + ")"
