from django.db import migrations

# legal_reference is deliberately vague: clause letters are NOT yet verified
# against the gazette text of the Rules, 2011.
RULES = [
    ("R01", "Manufacturer / packer / importer name and address",
     "Label names who made, packed or imported the product, with an address.",
     "Rule 6 (clause to verify)", "critical", ["manufacturer"]),
    ("R03", "Net quantity declared",
     "Label states the net quantity as a number with a unit.",
     "Rule 6 (clause to verify)", "critical", ["net_quantity"]),
    ("R05", "Month and year of manufacture / packing",
     "Label shows when the product was manufactured or packed.",
     "Rule 6 (clause to verify)", "major", ["mfg_date"]),
    ("R06", "MRP in rupees, inclusive of all taxes",
     "Label shows the maximum retail price in rupees, stated as inclusive of all taxes.",
     "Rule 6 (clause to verify)", "critical", ["mrp", "mrp_tax_note"]),
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
    dependencies = [("rules", "0001_initial")]
    operations = [migrations.RunPython(seed, migrations.RunPython.noop)]
