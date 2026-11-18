"""Reads the labelled test set: evaluation/data/cases.csv plus the files it points to.

One row = one product. `input` is a .txt file (typed label text) or one or more images
separated by ";" (all sides of one pack). Rule columns (R01..M02) hold the verdict the rule
SHOULD give: PASS, FAIL or CANNOT_DETERMINE. A blank cell means "not labelled", so it is
not scored.
"""
import csv
import re
from dataclasses import dataclass, field
from pathlib import Path

DATA_DIR = Path(__file__).resolve().parent / "data"
VERDICTS = {"PASS", "FAIL", "CANNOT_DETERMINE"}
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tif", ".tiff"}
RULE_COLUMN = re.compile(r"[RM]\d{2}")


class DatasetError(ValueError):
    """A problem in cases.csv, reported with the line number so it is easy to fix."""


@dataclass
class Case:
    id: str
    inputs: list                      # Paths to the .txt file or the images
    is_imported: bool | None          # the answer an officer would give on upload
    synthetic: bool                   # made-up label (True) or a real pack (False)
    expected: dict = field(default_factory=dict)  # rule code -> expected verdict
    notes: str = ""

    @property
    def kind(self):
        return "image" if self.inputs[0].suffix.lower() in IMAGE_SUFFIXES else "text"


def _yes_no(value):
    return {"yes": True, "no": False}.get(value.strip().lower())


def load_cases(csv_path=None):
    """Return the list of Case objects, or raise DatasetError naming the bad line."""
    csv_path = Path(csv_path) if csv_path else DATA_DIR / "cases.csv"
    if not csv_path.exists():
        raise DatasetError(f"{csv_path} not found.")
    base = csv_path.parent  # file paths in the CSV are relative to the CSV itself
    cases = []
    with open(csv_path, encoding="utf-8-sig", newline="") as f:  # -sig: Excel adds a BOM
        for line_no, row in enumerate(csv.DictReader(f), start=2):
            where = f"{csv_path.name} line {line_no}"
            inputs = [base / p.strip() for p in (row.get("input") or "").split(";") if p.strip()]
            if not inputs:
                raise DatasetError(f"{where}: the input column is empty.")
            missing = [str(p) for p in inputs if not p.exists()]
            if missing:
                raise DatasetError(f"{where}: file not found: {', '.join(missing)}")
            if len({p.suffix.lower() in IMAGE_SUFFIXES for p in inputs}) > 1:
                raise DatasetError(f"{where}: mix of text and image inputs; use one kind per case.")
            expected = {}
            for column, value in row.items():
                if column and RULE_COLUMN.fullmatch(column) and value and value.strip():
                    verdict = value.strip().upper()
                    if verdict not in VERDICTS:
                        raise DatasetError(f"{where}: {column} is '{value}', expected PASS, FAIL or CANNOT_DETERMINE.")
                    expected[column] = verdict
            cases.append(Case(
                id=row.get("id") or f"line{line_no}",
                inputs=inputs,
                is_imported=_yes_no(row.get("is_imported") or ""),
                synthetic=(row.get("synthetic") or "").strip().lower() == "yes",
                expected=expected,
                notes=row.get("notes") or "",
            ))
    return cases
