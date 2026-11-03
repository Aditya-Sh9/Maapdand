"""One small function per rule. Each takes an ExtractionResult and returns a RuleOutcome."""
import re

from extraction.parsers import has_pin_code, split_quantity, split_unit_sale_price

from .registry import register
from .units import BIG_UNIT_THRESHOLD, NON_STANDARD, describe
from .verdicts import RuleOutcome, Verdict

_CURRENCY = re.compile(r"₹|\brs\b|\binr\b|रु", re.IGNORECASE)


@register("R01")
def check_manufacturer_details(result):
    """The label must name the manufacturer, packer or importer and give an address."""
    found = result.get("manufacturer")
    if found is None:
        return RuleOutcome(Verdict.FAIL, "No 'Manufactured / Packed / Imported by' statement found.")
    evidence = {"manufacturer": found.value}
    if has_pin_code(found.value):
        return RuleOutcome(Verdict.PASS, "Manufacturer / packer statement with a PIN code found.", evidence)
    # A name without a PIN code may still be a full address; we can't tell, so we don't pass it.
    return RuleOutcome(
        Verdict.CANNOT_DETERMINE,
        "Statement found but no 6-digit PIN code, so the address may be incomplete. Check manually.",
        evidence,
    )


@register("R03")
def check_net_quantity_declared(result):
    """The label must declare the net quantity, e.g. 'Net Wt. 250 g'."""
    found = result.get("net_quantity")
    if found is None:
        return RuleOutcome(Verdict.FAIL, "No net quantity (number with unit) found.")
    return RuleOutcome(Verdict.PASS, "Net quantity declared.", {"net_quantity": found.value})


@register("R05")
def check_manufacture_date(result):
    """The label must show the month and year of manufacture (a packing date alone is not enough)."""
    found = result.get("mfg_date")
    if found is not None:
        return RuleOutcome(Verdict.PASS, "Month/year of manufacture declared.", {"mfg_date": found.value})
    packed = result.get("packed_date")
    if packed is not None:
        # Since 2021 the rule asks for the manufacture date; some labels still print only "Packed on".
        return RuleOutcome(
            Verdict.CANNOT_DETERMINE,
            "Only a packing date was found; the rule asks for the month/year of manufacture. Check manually.",
            {"packed_date": packed.value},
        )
    return RuleOutcome(Verdict.FAIL, "No month/year of manufacture found.")


@register("R06")
def check_mrp(result):
    """MRP must be present, in rupees, and stated as inclusive of all taxes."""
    mrp = result.get("mrp")
    if mrp is None:
        return RuleOutcome(Verdict.FAIL, "No MRP found.")
    evidence = {"mrp": mrp.value}
    if not _CURRENCY.search(mrp.value):
        return RuleOutcome(Verdict.FAIL, "MRP found but without a rupee sign (₹ / Rs.).", evidence)
    tax_note = result.get("mrp_tax_note")
    if tax_note is None:
        return RuleOutcome(Verdict.FAIL, "MRP is not stated as 'inclusive of all taxes'.", evidence)
    evidence["tax_note"] = tax_note.value
    return RuleOutcome(Verdict.PASS, "MRP in rupees and inclusive of all taxes.", evidence)


@register("R02")
def check_generic_name(result):
    """The label must state the common or generic name of the product, e.g. 'Roasted Peanuts'."""
    found = result.get("generic_name")
    if found is None:
        # Most labels print the name as a heading with no "Product name:" keyword, and text
        # matching can't tell that apart from a slogan, so a reviewer must confirm it.
        return RuleOutcome(Verdict.CANNOT_DETERMINE, "No labelled product name found. Confirm the generic name manually.")
    return RuleOutcome(Verdict.PASS, "Generic / product name declared.", {"generic_name": found.value})


def _parsed_quantity(result):
    """Net quantity as (dimension, amount in base units, is_big_unit, unit), or None."""
    found = result.get("net_quantity")
    parsed = split_quantity(found.value) if found else None
    described = describe(*parsed) if parsed else None
    return (*described, parsed[1]) if described else None


@register("R04")
def check_net_quantity_units(result):
    """Net quantity must use SI units: g/ml/cm under 1 kg/L/m, kg/L/m from there up, and no 'approx.'."""
    qualifier = result.get("quantity_qualifier")
    if qualifier is not None:
        return RuleOutcome(Verdict.FAIL, "Quantity is qualified by a word like 'approx.' or 'minimum'.",
                           {"quantity_qualifier": qualifier.value})
    quantity = _parsed_quantity(result)
    if quantity is None:
        return RuleOutcome(Verdict.CANNOT_DETERMINE, "No net quantity with a known unit to check (see R03).")
    dimension, base_amount, is_big, unit = quantity
    evidence = {"net_quantity": result.get("net_quantity").value}
    if unit in NON_STANDARD:
        return RuleOutcome(Verdict.FAIL, f"'{unit}' is not an SI symbol; it should be '{NON_STANDARD[unit]}'.", evidence)
    if unit == "mg":  # mostly medicines, where the drug rules decide
        return RuleOutcome(Verdict.CANNOT_DETERMINE, "Quantity in mg; check whether another law applies.", evidence)
    threshold = BIG_UNIT_THRESHOLD.get(dimension)
    if threshold and is_big and base_amount < threshold:
        return RuleOutcome(Verdict.FAIL, "Below 1 kg / 1 L / 1 m the quantity must be in g / ml / cm.", evidence)
    if threshold and not is_big and base_amount > threshold:  # exactly 1 kg may be written 1000 g
        return RuleOutcome(Verdict.FAIL, "From 1 kg / 1 L / 1 m up the quantity must be in kg / L / m.", evidence)
    return RuleOutcome(Verdict.PASS, "Net quantity uses a standard unit of the right size.", evidence)


@register("R07")
def check_consumer_care(result):
    """The label must give a phone number (and email, if available) for consumer complaints."""
    care, phone, email = result.get("consumer_care"), result.get("phone"), result.get("email")
    evidence = {name: f.value for name, f in [("consumer_care", care), ("phone", phone), ("email", email)] if f}
    if phone is None:
        return RuleOutcome(Verdict.FAIL, "No telephone number for consumer complaints found.", evidence)
    if care is None:
        # A number with no "Customer care" heading could be a factory or fax line.
        return RuleOutcome(Verdict.CANNOT_DETERMINE, "Phone number found but not marked as consumer care.", evidence)
    return RuleOutcome(Verdict.PASS, "Consumer care details with a phone number found.", evidence)


@register("R08")
def check_country_of_origin(result):
    """Imported products must state the country of origin, manufacture or assembly."""
    imported, origin = result.get("import_statement"), result.get("country_of_origin")
    if imported is None:
        # No importer named: the label presents the product as Indian, so the rule doesn't apply.
        return RuleOutcome(Verdict.PASS, "Not applicable: no importer named on the label.")
    evidence = {"import_statement": imported.value}
    if origin is None:
        return RuleOutcome(Verdict.FAIL, "Imported product without a country of origin.", evidence)
    evidence["country_of_origin"] = origin.value
    return RuleOutcome(Verdict.PASS, "Imported product states its country of origin.", evidence)


@register("R09")
def check_unit_sale_price(result):
    """Unit sale price must be per g under 1 kg and per kg over 1 kg (same for ml/L, cm/m), or per item."""
    quantity = _parsed_quantity(result)
    usp = result.get("unit_sale_price")
    if usp is None:
        if quantity and quantity[0] == "number" and quantity[1] == 1:
            return RuleOutcome(Verdict.PASS, "Not required: a single item, so MRP equals the unit sale price.")
        return RuleOutcome(Verdict.FAIL, "No unit sale price found (only combination, group or multi-piece "
                                         "packs are exempt).")
    evidence = {"unit_sale_price": usp.value}
    parsed = split_unit_sale_price(usp.value)
    per = describe(parsed[1], parsed[2]) if parsed else None  # the "100 g" in "₹48 per 100 g"
    if quantity is None or per is None:
        return RuleOutcome(Verdict.CANNOT_DETERMINE, "Unit sale price found but could not be compared with the "
                                                     "net quantity.", evidence)
    if per[0] != quantity[0]:
        return RuleOutcome(Verdict.FAIL, "Unit sale price uses a different kind of unit from the net quantity.", evidence)
    threshold = BIG_UNIT_THRESHOLD.get(quantity[0])
    if threshold is None:  # sold by number: any "per item" is fine
        return RuleOutcome(Verdict.PASS, "Unit sale price per item declared.", evidence)
    per_is_big = per[2]
    wrong_base = (
        parsed[1] != 1  # "per 100 g" is not "per g"
        or (quantity[1] < threshold and per_is_big)
        or (quantity[1] > threshold and not per_is_big)  # exactly 1 kg: either base is accepted
    )
    if wrong_base:
        return RuleOutcome(Verdict.FAIL, "Unit sale price must be per g / ml / cm under 1 kg / L / m and per "
                                         "kg / L / m above.", evidence)
    return RuleOutcome(Verdict.PASS, "Unit sale price declared on the right base.", evidence)


@register("R10")
def check_best_before(result):
    """Products that can go bad must show a 'best before' or 'use by' date."""
    found = result.get("best_before")
    if found is None:
        # Needed only for perishables, and for food the FSS rules decide; text can't tell
        # us the product type, so a missing date is flagged for review, not failed.
        return RuleOutcome(Verdict.CANNOT_DETERMINE, "No best before / use by date found. Required only if the "
                                                     "product can become unfit for use; check manually.")
    return RuleOutcome(Verdict.PASS, "Best before / use by date declared.", {"best_before": found.value})


@register("M01")
def check_letter_height(result):
    """Letters and numerals must meet the minimum height for the display panel's area."""
    return RuleOutcome(Verdict.CANNOT_DETERMINE, "Letter height needs a measured image and panel size; check manually.")


@register("M02")
def check_principal_display_panel(result):
    """All declarations must appear on the principal display panel."""
    return RuleOutcome(Verdict.CANNOT_DETERMINE, "Text alone can't show which side of the pack it came from; check manually.")
