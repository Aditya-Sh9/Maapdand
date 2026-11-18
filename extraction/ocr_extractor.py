"""Reads label photos with Tesseract, then reuses the text parsers on what it read.

Same interface as TextExtractor, so the rules cannot tell the difference.
"""
import os
import re

import pytesseract
from django.conf import settings

from .base import BaseExtractor, ExtractedValue, ExtractionResult
from .preprocess import load_image, preprocess
from .text_extractor import TextExtractor


def _clean(token):
    """Lowercase and drop punctuation so 'MRP:' and 'mrp' compare equal."""
    return re.sub(r"[^\w]", "", token.lower())


def read_words(img):
    """Run Tesseract on one preprocessed image.
    Returns (words, text). Each word is {text, conf (0..1), box (pixels), line}."""
    pytesseract.pytesseract.tesseract_cmd = settings.TESSERACT_CMD
    # Tesseract looks for its language files in the folder named by this variable.
    os.environ["TESSDATA_PREFIX"] = str(settings.TESSDATA_DIR)
    data = pytesseract.image_to_data(
        img, lang=settings.OCR_LANGUAGES, output_type=pytesseract.Output.DICT
    )
    words = []
    for i, text in enumerate(data["text"]):
        text = text.strip()
        conf = float(data["conf"][i])
        if not text or conf < 0:  # Tesseract uses -1 for "not a word"
            continue
        words.append({
            "text": text,
            "conf": conf / 100,
            "box": (data["left"][i], data["top"][i], data["width"][i], data["height"][i]),
            "line": (data["block_num"][i], data["par_num"][i], data["line_num"][i]),
        })

    # Rebuild the text line by line so the parsers see normal looking lines.
    lines, order = {}, []
    for w in words:
        if w["line"] not in lines:
            lines[w["line"]] = []
            order.append(w["line"])
        lines[w["line"]].append(w["text"])
    text = "\n".join(" ".join(lines[key]) for key in order)
    return words, text


def locate(value, words, image_size):
    """Best-effort: find the OCR words that spell `value` and return their combined box
    as fractions of the image, plus the average confidence of those words.
    Returns (bbox or None, confidence or None). Parsers may tidy a value, so a miss is normal."""
    targets = [_clean(t) for t in value.split() if _clean(t)]
    if not targets:
        return None, None
    # Skip punctuation-only words ("&", "-") on both sides, or a value like
    # "Mfd. & Packed by" would stop matching at the "&".
    words = [w for w in words if _clean(w["text"])]
    cleaned = [_clean(w["text"]) for w in words]

    best = []  # longest run of consecutive words matching the start of the value
    for start in range(len(words)):
        run = []
        for offset, target in enumerate(targets):
            pos = start + offset
            if pos < len(words) and cleaned[pos] == target:
                run.append(words[pos])
            else:
                break
        if len(run) > len(best):
            best = run
    if not best:
        return None, None

    left = min(w["box"][0] for w in best)
    top = min(w["box"][1] for w in best)
    right = max(w["box"][0] + w["box"][2] for w in best)
    bottom = max(w["box"][1] + w["box"][3] for w in best)
    width, height = image_size
    bbox = [left / width, top / height, (right - left) / width, (bottom - top) / height]
    return bbox, sum(w["conf"] for w in best) / len(best)


class OCRExtractor(BaseExtractor):
    """`source` is a list of image file paths (one product = one or more images)."""

    def extract(self, source):
        text_extractor = TextExtractor()
        image_texts = []
        best = {}  # field name -> ExtractedValue, keeping the most confident find

        for index, path in enumerate(source):
            prepared = preprocess(load_image(path))
            words, text = read_words(prepared)
            image_texts.append(text)
            average = sum(w["conf"] for w in words) / len(words) if words else 0.0

            for name, found in text_extractor.extract(text).fields.items():
                bbox, confidence = locate(found.value, words, prepared.size)
                candidate = ExtractedValue(
                    value=found.value,
                    # If we could not pin the words down, fall back to the image average.
                    confidence=round(confidence if confidence is not None else average, 2),
                    bbox=bbox,
                    image_index=index,
                )
                # A field found in any image counts; if several have it, keep the surest.
                if name not in best or candidate.confidence > best[name].confidence:
                    best[name] = candidate

        return ExtractionResult(
            raw_text="\n\n".join(image_texts), fields=best, image_texts=image_texts
        )
