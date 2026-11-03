"""One small function per rule. Each takes an ExtractionResult and returns a RuleOutcome."""
import re

from extraction.parsers import has_pin_code

from .registry import register
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
    """The label must show the month and year of manufacture or packing."""
    found = result.get("mfg_date")
    if found is None:
        return RuleOutcome(Verdict.FAIL, "No month/year of manufacture or packing found.")
    return RuleOutcome(Verdict.PASS, "Manufacture / packing date declared.", {"mfg_date": found.value})


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
