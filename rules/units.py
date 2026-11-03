"""What each unit on a label means, so rules R04 and R09 can compare quantities.

unit as written -> (dimension, how many base units it is). Base units: g, ml, cm, one item.
"""
from decimal import Decimal

UNITS = {
    "mg": ("mass", Decimal("0.001")),
    "g": ("mass", Decimal(1)), "gm": ("mass", Decimal(1)), "gms": ("mass", Decimal(1)),
    "ग्राम": ("mass", Decimal(1)),
    "kg": ("mass", Decimal(1000)), "किग्रा": ("mass", Decimal(1000)),
    "ml": ("volume", Decimal(1)), "मिली": ("volume", Decimal(1)),
    "l": ("volume", Decimal(1000)), "ltr": ("volume", Decimal(1000)), "लीटर": ("volume", Decimal(1000)),
    "litre": ("volume", Decimal(1000)), "litres": ("volume", Decimal(1000)),
    "liter": ("volume", Decimal(1000)), "liters": ("volume", Decimal(1000)),
    "cm": ("length", Decimal(1)),
    "m": ("length", Decimal(100)), "metre": ("length", Decimal(100)), "metres": ("length", Decimal(100)),
    "meter": ("length", Decimal(100)), "meters": ("length", Decimal(100)),
}
for _word in ["n", "u", "no", "nos", "number", "numbers", "pc", "pcs", "piece", "pieces",
              "pair", "pairs", "set", "sets", "unit", "units", "नग"]:
    UNITS[_word] = ("number", Decimal(1))

# Rule 13: below this many base units use the small unit (g, ml, cm), at or above use the big one.
BIG_UNIT_THRESHOLD = {"mass": Decimal(1000), "volume": Decimal(1000), "length": Decimal(100)}

# Common spellings that are not SI symbols -> the symbol the label should use.
NON_STANDARD = {"gm": "g", "gms": "g", "ltr": "l"}


def describe(amount, unit):
    """(250, 'g') -> ('mass', Decimal('250') in base units, is_big_unit). None if unit unknown."""
    if unit not in UNITS:
        return None
    dimension, factor = UNITS[unit]
    threshold = BIG_UNIT_THRESHOLD.get(dimension)
    is_big = threshold is not None and factor >= threshold
    return dimension, amount * factor, is_big
