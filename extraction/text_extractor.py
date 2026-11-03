from . import parsers
from .base import BaseExtractor, ExtractedValue, ExtractionResult

# field name -> parser. Adding a field later means adding one line here.
_PARSERS = {
    "manufacturer": parsers.find_manufacturer,
    "net_quantity": parsers.find_net_quantity,
    "mfg_date": parsers.find_mfg_date,
    "mrp": parsers.find_mrp,
    "mrp_tax_note": parsers.find_mrp_tax_note,
}


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
