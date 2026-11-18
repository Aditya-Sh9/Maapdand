from . import parsers
from .base import BaseExtractor, ExtractedValue, ExtractionResult

# field name -> parser. Adding a field later means adding one line here.
_PARSERS = {
    "manufacturer": parsers.find_manufacturer,
    "import_statement": parsers.find_import_statement,
    "generic_name": parsers.find_generic_name,
    "net_quantity": parsers.find_net_quantity,
    "quantity_qualifier": parsers.find_quantity_qualifier,
    "mfg_date": parsers.find_mfg_date,
    "packed_date": parsers.find_packed_date,
    "best_before": parsers.find_best_before,
    "mrp": parsers.find_mrp,
    "mrp_tax_note": parsers.find_mrp_tax_note,
    "unit_sale_price": parsers.find_unit_sale_price,
    "consumer_care": parsers.find_consumer_care,
    "email": parsers.find_email,
    "phone": parsers.find_phone,
    "country_of_origin": parsers.find_country_of_origin,
}

FIELD_NAMES = list(_PARSERS)  # used by the review page to list every field, found or not


class TextExtractor(BaseExtractor):
    """Extracts fields from text the user typed or pasted."""

    def extract(self, source):
        text = parsers.normalize_text(source)
        result = ExtractionResult(raw_text=text)
        for name, parse in _PARSERS.items():
            found = parse(text)
            if found:
                result.fields[name] = ExtractedValue(value=found)
        return result
