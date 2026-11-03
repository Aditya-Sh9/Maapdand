from django.db import migrations

# Clauses checked against the gazette PDFs in docs/reference/ (Rules 2011 + amendments
# up to 21 Sep 2026). "PCR" = Legal Metrology (Packaged Commodities) Rules, 2011.
RULES = [
    ("R01", "Manufacturer / packer / importer name and address",
     "Label names who made, packed or imported the product, with a complete address.",
     "PCR Rule 6(1)(a), Rule 10(1)", "critical",
     ["manufacturer"]),
    ("R02", "Common or generic name",
     "Label states the common or generic name of the product.",
     "PCR Rule 6(1)(b)", "major",
     ["generic_name"]),
    ("R03", "Net quantity declared",
     "Label states the net quantity as a number with a unit.",
     "PCR Rule 6(1)(c)", "critical",
     ["net_quantity"]),
    ("R04", "Net quantity in standard units",
     "SI units; g/ml/cm below 1 kg/L/m and kg/L/m from there up; no 'approx.' or 'minimum'.",
     "PCR Rules 12(6), 13", "major",
     ["net_quantity", "quantity_qualifier"]),
    ("R05", "Month and year of manufacture",
     "Label shows the month and year the product was manufactured.",
     "PCR Rule 6(1)(d) (as amended 2021)", "major",
     ["mfg_date", "packed_date"]),
    ("R06", "MRP inclusive of all taxes",
     "Label shows the maximum retail price in rupees, stated as inclusive of all taxes.",
     "PCR Rule 6(1)(e), Rule 2(m)", "critical",
     ["mrp", "mrp_tax_note"]),
    ("R07", "Consumer care details",
     "Label gives a phone number (and email, if available) for consumer complaints.",
     "PCR Rule 6(2)", "major",
     ["consumer_care", "phone", "email"]),
    ("R08", "Country of origin (imported products)",
     "Imported products state the country of origin, manufacture or assembly.",
     "PCR Rule 6(1)(aa) (inserted 2017)", "major",
     ["import_statement", "country_of_origin"]),
    ("R09", "Unit sale price",
     "Unit sale price per g/kg, ml/L, cm/m or per item, matched to the net quantity.",
     "PCR Rule 6(11) (as substituted 2022)", "major",
     ["unit_sale_price", "net_quantity"]),
    ("R10", "Best before / use by date",
     "Products that can become unfit for use show a best before or use by date.",
     "PCR Rule 6(1)(da) (inserted 2017)", "minor",
     ["best_before"]),
    ("M01", "Letter and numeral height",
     "Minimum height of letters and numerals for the principal display panel's area. Needs measurement.",
     "PCR Rule 7(2), Table I (as substituted 2017)", "minor",
     []),
    ("M02", "Declarations on principal display panel",
     "All declarations appear on the principal display panel. Needs the package, not just text.",
     "PCR Rule 8(1)", "minor",
     []),
]


def seed(apps, schema_editor):
    Rule = apps.get_model("rules", "Rule")
    for code, title, description, ref, severity, fields in RULES:
        Rule.objects.update_or_create(
            code=code,
            defaults=dict(title=title, description=description, legal_reference=ref,
                          severity=severity, required_fields=fields),
        )


class Migration(migrations.Migration):
    dependencies = [("rules", "0002_seed_rules")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
